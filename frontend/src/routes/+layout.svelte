<script lang="ts">
	import '../app.css';
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';
	import { api } from '$lib/api';
	import { updates } from '$lib/stores/updates';

	let menuOpen = false;
	let sidebarOpen = false;
	let updatesOpen = false;
	let updatesLoading = false;
	let headerSearchQuery = '';

	// Subscribe to store
	$: recentUpdates = $updates;
	$: unreadUpdatesCount = $updates.length;

	// List of public routes that don't require authentication
	const publicRoutes = ['/login', '/about', '/colophon'];

	// Check if current path is a username profile page (starts with / and is a single segment)
	function isPublicProfilePage(pathname: string): boolean {
		// Match /{username} but not /login, /about, /colophon, /show, /checkins, /settings
		const segments = pathname.split('/').filter(s => s.length > 0);
		if (segments.length !== 1) return false;

		const knownRoutes = ['login', 'about', 'colophon', 'show', 'checkins', 'settings', 'swanson', 'watchlist', 'person'];
		return !knownRoutes.includes(segments[0]);
	}

	// Load updates into store
	async function loadUpdates() {
		if (updatesLoading) return;
		updatesLoading = true;
		try {
			await updates.load(true, 10);
		} finally {
			updatesLoading = false;
		}
	}

	// Toggle updates dropdown
	async function toggleUpdates() {
		updatesOpen = !updatesOpen;
		menuOpen = false; // Close user menu if open
		if (updatesOpen) {
			// Always fetch fresh data when opening
			await loadUpdates();
		}
	}

	// Mark update as read
	async function markAsRead(updateId: number) {
		await updates.markAsRead(updateId);
	}

	// Format relative time
	function formatRelativeTime(dateStr: string): string {
		const date = new Date(dateStr);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffMins = Math.floor(diffMs / 60000);
		const diffHours = Math.floor(diffMs / 3600000);
		const diffDays = Math.floor(diffMs / 86400000);

		if (diffMins < 60) return `${diffMins}m ago`;
		if (diffHours < 24) return `${diffHours}h ago`;
		if (diffDays < 7) return `${diffDays}d ago`;
		return date.toLocaleDateString();
	}

	// Check authentication on mount - validate token and redirect to login if invalid
	onMount(async () => {
		const isPublic = publicRoutes.includes($page.url.pathname) || isPublicProfilePage($page.url.pathname);

		// Use isValid() which checks expiration and clears auth if expired
		if (!auth.isValid() && !isPublic) {
			goto('/login');
		}

		// Load updates into store and start polling
		await loadUpdates();
		updates.startPolling(30000); // Poll every 30 seconds

		// Close menus on ESC key
		function handleKeydown(event: KeyboardEvent) {
			if (event.key === 'Escape') {
				menuOpen = false;
				updatesOpen = false;
			}
		}

		window.addEventListener('keydown', handleKeydown);
		return () => window.removeEventListener('keydown', handleKeydown);
	});

	// Stop polling on destroy
	onDestroy(() => {
		updates.stopPolling();
	});

	// Reactive: redirect to home if authenticated and on login page
	$: if ($auth.token && $page.url.pathname === '/login') {
		menuOpen = false;
		goto('/');
	}

	// Close menus when navigating to a different page
	$: if ($page.url.pathname) {
		menuOpen = false;
		updatesOpen = false;
		sidebarOpen = false;
	}

	async function handleLogout() {
		try {
			await api.auth.logout();
		} catch (err) {
			// Ignore error, logout anyway
		}
		auth.logout();
		goto('/login');
	}

	function handleHeaderSearch(event: Event) {
		event.preventDefault();
		if (!headerSearchQuery.trim()) return;
		goto(`/?q=${encodeURIComponent(headerSearchQuery)}`);
		headerSearchQuery = '';
	}

	// Detect if on front page
	$: isHomePage = $page.url.pathname === '/';
</script>

{#if $page.url.pathname === '/login'}
	<slot />
{:else if isPublicProfilePage($page.url.pathname)}
	<!-- Public profile page - render without authentication -->
	<slot />
{:else if $auth.user}
	<div class="min-h-screen bg-gray-50">
		<!-- Sidebar overlay -->
		{#if sidebarOpen}
			<div
				class="fixed inset-0 bg-gray-600 bg-opacity-50 z-30"
				on:click={() => sidebarOpen = false}
				on:keydown={(e) => e.key === 'Escape' && (sidebarOpen = false)}
				role="button"
				tabindex="0"
				aria-label="Close sidebar"
			></div>
		{/if}

		<!-- Collapsible Sidebar -->
		<aside
			class="fixed inset-y-0 left-0 z-40 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out"
			class:-translate-x-full={!sidebarOpen}
			class:translate-x-0={sidebarOpen}
		>
			<div class="flex flex-col h-full">
				<!-- Sidebar header with logo -->
				<div class="flex items-center justify-between h-16 px-4 border-b border-gray-200">
					<a href="/" class="flex items-center gap-3">
						<img src="https://swm.cc/projects/whatisonthe-tv.svg" alt="What Is On The TV" width="36" height="36" />
						<span class="font-semibold text-gray-900 text-sm">What Is On The TV</span>
					</a>
					<button
						on:click={() => sidebarOpen = false}
						class="p-1 text-gray-400 hover:text-gray-600"
					>
						<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>

				<!-- Navigation links -->
				<nav class="flex-1 px-4 py-6 space-y-2">
					<a
						href="/"
						class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
						class:bg-indigo-50={isHomePage}
						class:text-indigo-700={isHomePage}
						class:text-gray-700={!isHomePage}
						class:hover:bg-gray-100={!isHomePage}
						on:click={() => sidebarOpen = false}
					>
						<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
						</svg>
						Home
					</a>
					<a
						href="/checkins"
						class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
						class:bg-indigo-50={$page.url.pathname === '/checkins'}
						class:text-indigo-700={$page.url.pathname === '/checkins'}
						class:text-gray-700={$page.url.pathname !== '/checkins'}
						class:hover:bg-gray-100={$page.url.pathname !== '/checkins'}
						on:click={() => sidebarOpen = false}
					>
						<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
						</svg>
						Check-ins
					</a>
					<a
						href="/watchlist"
						class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
						class:bg-indigo-50={$page.url.pathname === '/watchlist'}
						class:text-indigo-700={$page.url.pathname === '/watchlist'}
						class:text-gray-700={$page.url.pathname !== '/watchlist'}
						class:hover:bg-gray-100={$page.url.pathname !== '/watchlist'}
						on:click={() => sidebarOpen = false}
					>
						<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
						</svg>
						Watchlist
					</a>

					<!-- Updates/Notifications (only shown when there are updates) -->
					{#if unreadUpdatesCount > 0}
						<button
							on:click={toggleUpdates}
							class="w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-gray-700 hover:bg-gray-100"
						>
							<div class="flex items-center gap-3">
								<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
								</svg>
								Updates
							</div>
							<span class="flex items-center justify-center h-5 min-w-5 px-1.5 rounded-full bg-red-500 text-white text-xs font-medium">
								{unreadUpdatesCount > 99 ? '99+' : unreadUpdatesCount}
							</span>
						</button>

						<!-- Updates dropdown panel -->
						{#if updatesOpen}
						<div class="mt-2 mx-2 rounded-lg border border-gray-200 bg-gray-50 overflow-hidden">
							<div class="px-3 py-2 border-b border-gray-200 flex items-center justify-between bg-white">
								<span class="text-xs font-semibold text-gray-700">Recent Updates</span>
								<a href="/watchlist" class="text-xs text-indigo-600 hover:text-indigo-800" on:click={() => sidebarOpen = false}>View all</a>
							</div>
							{#if updatesLoading}
								<div class="px-3 py-6 text-center">
									<svg class="animate-spin h-5 w-5 text-indigo-600 mx-auto" viewBox="0 0 24 24">
										<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
										<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
									</svg>
								</div>
							{:else if recentUpdates.length === 0}
								<div class="px-3 py-4 text-center text-xs text-gray-500">
									No updates yet
								</div>
							{:else}
								<div class="max-h-48 overflow-y-auto">
									{#each recentUpdates.slice(0, 5) as update}
										<div class="px-3 py-2 hover:bg-white border-b border-gray-100 last:border-0">
											<p class="text-xs text-gray-700 line-clamp-2">{update.description}</p>
											<p class="text-xs text-gray-400 mt-0.5">{formatRelativeTime(update.created_at)}</p>
										</div>
									{/each}
								</div>
							{/if}
						</div>
						{/if}
					{/if}
				</nav>

				<!-- User section at bottom -->
				<div class="border-t border-gray-200 p-4">
					<div class="flex items-center gap-3">
						<div class="h-10 w-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-medium flex-shrink-0">
							{$auth.user.first_name[0]}{$auth.user.last_name[0]}
						</div>
						<div class="min-w-0">
							<p class="text-sm font-medium text-gray-900 truncate">
								{$auth.user.first_name} {$auth.user.last_name}
							</p>
							{#if $auth.user.username}
								<p class="text-xs text-indigo-600 truncate">@{$auth.user.username}</p>
							{/if}
						</div>
					</div>
					<div class="mt-4 space-y-1">
						<a
							href="/settings"
							class="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
							on:click={() => sidebarOpen = false}
						>
							<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
							</svg>
							Settings
						</a>
						<button
							on:click={handleLogout}
							class="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
						>
							<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
							</svg>
							Sign Out
						</button>
					</div>
				</div>
			</div>
		</aside>

		<!-- Main content area with top bar -->
		<div>
			<!-- Top navigation bar -->
			<nav class="bg-white shadow-sm sticky top-0 z-20">
				<div class="px-3 sm:px-6 lg:px-8">
					<div class="flex items-center justify-between h-16 gap-3">
						<!-- Left: Hamburger + Logo -->
						<div class="flex items-center gap-2 flex-shrink-0">
							<button
								on:click={() => sidebarOpen = !sidebarOpen}
								class="relative p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
							>
								<span class="sr-only">Toggle sidebar</span>
								<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
								</svg>
								<!-- Pulsing notification indicator when sidebar closed and has unread updates -->
								{#if !sidebarOpen && unreadUpdatesCount > 0}
									<span class="absolute top-1 right-1 flex h-3 w-3">
										<span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
										<span class="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
									</span>
								{/if}
							</button>

							<a href="/" class="flex items-center">
								<img src="https://swm.cc/projects/whatisonthe-tv.svg" alt="What Is On The TV" width="32" height="32" />
							</a>
						</div>

						<!-- Center: Search bar (only shown when NOT on home page) -->
						{#if !isHomePage}
							<form on:submit={handleHeaderSearch} class="flex-1 max-w-2xl mx-auto">
								<div class="relative w-full">
									<div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
										<svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
										</svg>
									</div>
									<input
										type="text"
										bind:value={headerSearchQuery}
										placeholder="Search..."
										class="w-full pl-11 pr-4 py-2.5 text-base rounded-full border border-gray-300 shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
									/>
								</div>
							</form>
						{/if}

					</div>
				</div>
			</nav>

			<!-- Main content -->
			<main>
				<slot />
			</main>

			<!-- Footer -->
			<footer class="mt-24 border-t border-gray-200">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
				<div class="flex flex-col md:flex-row justify-between items-center gap-4">
					<div class="flex gap-6 text-sm">
						<a href="/about" class="text-gray-600 hover:text-indigo-600 transition-colors">About</a>
						<a href="/colophon" class="text-gray-600 hover:text-indigo-600 transition-colors">Colophon</a>
					</div>
					<p class="text-sm text-gray-600">
						Built with ❤️ by <a href="https://swm.cc" class="text-indigo-600 hover:text-indigo-500 transition-colors" target="_blank" rel="noopener noreferrer">swmcc</a>
					</p>
				</div>
			</div>
			</footer>
		</div>
	</div>
{/if}
