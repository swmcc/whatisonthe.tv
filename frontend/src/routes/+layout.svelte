<script lang="ts">
	import '../app.css';
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';
	import { api } from '$lib/api';
	import { updates } from '$lib/stores/updates';

	let menuOpen = false;
	let updatesOpen = false;
	let updatesLoading = false;

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
</script>

{#if $page.url.pathname === '/login'}
	<slot />
{:else if isPublicProfilePage($page.url.pathname)}
	<!-- Public profile page - render without authentication -->
	<slot />
{:else if $auth.user}
	<div class="min-h-screen bg-gray-50">
		<!-- Navigation -->
		<nav class="bg-white shadow-sm">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div class="flex justify-between h-16">
					<div class="flex">
						<div class="flex-shrink-0 flex items-center">
							<a href="/" class="flex items-center">
								<img src="https://swm.cc/projects/whatisonthe-tv.svg" alt="What Is On The TV" width="40" height="40" />
							</a>
						</div>
						<div class="hidden sm:ml-8 sm:flex sm:space-x-8">
							<a
								href="/"
								class="border-transparent text-gray-900 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium hover:border-indigo-500 transition-colors"
								class:border-indigo-500={$page.url.pathname === '/'}
								class:text-indigo-600={$page.url.pathname === '/'}
							>
								Search
							</a>
							<a
								href="/checkins"
								class="border-transparent text-gray-500 hover:text-gray-900 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium hover:border-indigo-500 transition-colors"
								class:border-indigo-500={$page.url.pathname === '/checkins'}
								class:text-indigo-600={$page.url.pathname === '/checkins'}
							>
								Check-ins
							</a>
							<a
								href="/watchlist"
								class="border-transparent text-gray-500 hover:text-gray-900 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium hover:border-indigo-500 transition-colors"
								class:border-indigo-500={$page.url.pathname === '/watchlist'}
								class:text-indigo-600={$page.url.pathname === '/watchlist'}
							>
								Watchlist
							</a>
						</div>
					</div>

					<div class="hidden sm:ml-6 sm:flex sm:items-center space-x-4">
						<!-- Updates notification bell -->
						{#if unreadUpdatesCount > 0}
							<div class="relative">
								<button
									on:click={toggleUpdates}
									class="relative p-1 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 rounded-full"
									title="Watchlist updates"
								>
									<span class="sr-only">View watchlist updates</span>
									<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
									</svg>
									<span class="absolute -top-1 -right-1 flex items-center justify-center h-5 w-5 rounded-full bg-red-500 text-white text-xs font-medium">
										{unreadUpdatesCount > 9 ? '9+' : unreadUpdatesCount}
									</span>
								</button>

								{#if updatesOpen}
									<div class="origin-top-right absolute right-0 mt-2 w-80 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-20">
										<div class="py-2">
											<div class="px-4 py-2 border-b border-gray-100 flex items-center justify-between">
												<h3 class="text-sm font-semibold text-gray-900">Watchlist Updates</h3>
												<a href="/watchlist" class="text-xs text-indigo-600 hover:text-indigo-800">View all</a>
											</div>

											{#if updatesLoading}
												<div class="px-4 py-8 text-center">
													<svg class="animate-spin h-6 w-6 text-indigo-600 mx-auto" viewBox="0 0 24 24">
														<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
														<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
													</svg>
												</div>
											{:else if recentUpdates.length === 0}
												<div class="px-4 py-6 text-center text-sm text-gray-500">
													No updates yet
												</div>
											{:else}
												<div class="max-h-80 overflow-y-auto">
													{#each recentUpdates as update}
														<div
															class="px-4 py-3 hover:bg-gray-50 border-b border-gray-50 last:border-0"
														>
															<div class="flex items-start gap-3">
																<!-- Thumbnail -->
																{#if update.watchlist_item?.content}
																	<a href="/show/{update.watchlist_item.content.tvdb_id}" class="flex-shrink-0">
																		<img
																			src={update.watchlist_item.content.image_url || update.watchlist_item.content.poster_url || 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="40" height="60"%3E%3Crect fill="%23e5e7eb" width="40" height="60"/%3E%3C/svg%3E'}
																			alt=""
																			class="w-10 h-14 object-cover rounded"
																		/>
																	</a>
																{:else if update.watchlist_item?.person}
																	<a href="/person/{update.watchlist_item.person.tvdb_id}" class="flex-shrink-0">
																		<img
																			src={update.watchlist_item.person.image_url || 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="40" height="40"%3E%3Crect fill="%23e5e7eb" width="40" height="40"/%3E%3C/svg%3E'}
																			alt=""
																			class="w-10 h-10 object-cover rounded-full"
																		/>
																	</a>
																{/if}

																<div class="flex-1 min-w-0">
																	<p class="text-sm text-gray-900 line-clamp-2">{update.description}</p>
																	<p class="text-xs text-gray-400 mt-1">{formatRelativeTime(update.created_at)}</p>
																</div>

																{#if !update.is_read}
																	<button
																		on:click|stopPropagation={() => markAsRead(update.id)}
																		class="flex-shrink-0 p-1 text-gray-400 hover:text-indigo-600"
																		title="Mark as read"
																	>
																		<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
																		</svg>
																	</button>
																{/if}
															</div>
														</div>
													{/each}
												</div>
											{/if}
										</div>
									</div>
								{/if}
							</div>
						{/if}

						<div class="relative">
							<button
								on:click={() => menuOpen = !menuOpen}
								class="flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 p-1"
							>
								<span class="sr-only">Open user menu</span>
								<div class="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center text-white font-medium">
									{$auth.user.first_name[0]}{$auth.user.last_name[0]}
								</div>
								<svg class="ml-2 h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
									<path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
								</svg>
							</button>

							{#if menuOpen}
								<div class="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-10">
									<div class="py-1">
										<div class="px-4 py-3 border-b border-gray-100">
											<p class="text-sm font-medium text-gray-900">
												{$auth.user.first_name} {$auth.user.last_name}
											</p>
											{#if $auth.user.username}
												<p class="text-xs text-indigo-600 font-medium">
													@{$auth.user.username}
												</p>
											{/if}
											<p class="text-xs text-gray-500 truncate">
												{$auth.user.email}
											</p>
										</div>
										<a
											href="/settings"
											class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
											on:click={() => menuOpen = false}
										>
											<span>⚙️</span>
											<span>Settings</span>
										</a>
										<button
											on:click={handleLogout}
											class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
										>
											<span>👋</span>
											<span>Sign Out</span>
										</button>
									</div>
								</div>
							{/if}
						</div>
					</div>

					<!-- Mobile menu button -->
					<div class="flex items-center sm:hidden">
						<button
							on:click={() => menuOpen = !menuOpen}
							class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
						>
							<span class="sr-only">Open main menu</span>
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								{#if !menuOpen}
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
								{:else}
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
								{/if}
							</svg>
						</button>
					</div>
				</div>
			</div>

			<!-- Mobile menu -->
			{#if menuOpen}
				<div class="sm:hidden">
					<div class="pt-2 pb-3 space-y-1">
						<a
							href="/"
							class="block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
							class:border-indigo-500={$page.url.pathname === '/'}
							class:bg-indigo-50={$page.url.pathname === '/'}
							class:text-indigo-700={$page.url.pathname === '/'}
							class:border-transparent={$page.url.pathname !== '/'}
							class:text-gray-600={$page.url.pathname !== '/'}
						>
							Search
						</a>
						<a
							href="/checkins"
							class="block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
							class:border-indigo-500={$page.url.pathname === '/checkins'}
							class:bg-indigo-50={$page.url.pathname === '/checkins'}
							class:text-indigo-700={$page.url.pathname === '/checkins'}
							class:border-transparent={$page.url.pathname !== '/checkins'}
							class:text-gray-600={$page.url.pathname !== '/checkins'}
						>
							Check-ins
						</a>
						<a
							href="/watchlist"
							class="block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
							class:border-indigo-500={$page.url.pathname === '/watchlist'}
							class:bg-indigo-50={$page.url.pathname === '/watchlist'}
							class:text-indigo-700={$page.url.pathname === '/watchlist'}
							class:border-transparent={$page.url.pathname !== '/watchlist'}
							class:text-gray-600={$page.url.pathname !== '/watchlist'}
						>
							Watchlist
						</a>
					</div>
					<div class="pt-4 pb-3 border-t border-gray-200">
						<div class="flex items-center px-4">
							<div class="flex-shrink-0">
								<div class="h-10 w-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-medium">
									{$auth.user.first_name[0]}{$auth.user.last_name[0]}
								</div>
							</div>
							<div class="ml-3">
								<div class="text-base font-medium text-gray-800">
									{$auth.user.first_name} {$auth.user.last_name}
								</div>
								{#if $auth.user.username}
									<div class="text-xs font-medium text-indigo-600">
										@{$auth.user.username}
									</div>
								{/if}
								<div class="text-sm font-medium text-gray-500">
									{$auth.user.email}
								</div>
							</div>
						</div>
						<div class="mt-3 space-y-1">
							<a
								href="/settings"
								class="flex items-center gap-2 px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
								on:click={() => menuOpen = false}
							>
								<span>⚙️</span>
								<span>Settings</span>
							</a>
							<button
								on:click={handleLogout}
								class="flex items-center gap-2 w-full text-left px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
							>
								<span>👋</span>
								<span>Sign Out</span>
							</button>
						</div>
					</div>
				</div>
			{/if}
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
{/if}
