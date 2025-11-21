<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';
	import { api } from '$lib/api';

	let menuOpen = false;

	// Check authentication on mount - just redirect to login if no token
	onMount(async () => {
		if (!$auth.token && $page.url.pathname !== '/login') {
			goto('/login');
		}

		// Close menu on ESC key
		function handleKeydown(event: KeyboardEvent) {
			if (event.key === 'Escape' && menuOpen) {
				menuOpen = false;
			}
		}

		window.addEventListener('keydown', handleKeydown);
		return () => window.removeEventListener('keydown', handleKeydown);
	});

	// Reactive: redirect to home if authenticated and on login page
	$: if ($auth.token && $page.url.pathname === '/login') {
		menuOpen = false;
		goto('/');
	}

	// Close menu when navigating to a different page
	$: if ($page.url.pathname) {
		menuOpen = false;
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
{:else if $auth.user}
	<div class="min-h-screen bg-gray-50">
		<!-- Navigation -->
		<nav class="bg-white shadow-sm">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div class="flex justify-between h-16">
					<div class="flex">
						<div class="flex-shrink-0 flex items-center">
							<a href="/" class="flex items-center">
								<!-- Retro TV SVG -->
								<svg width="40" height="40" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
									<!-- Antenna -->
									<line x1="35" y1="15" x2="25" y2="5" stroke="#8B4513" stroke-width="2" stroke-linecap="round"/>
									<line x1="65" y1="15" x2="75" y2="5" stroke="#8B4513" stroke-width="2" stroke-linecap="round"/>
									<circle cx="25" cy="5" r="2" fill="#8B4513"/>
									<circle cx="75" cy="5" r="2" fill="#8B4513"/>

									<!-- TV Body -->
									<rect x="15" y="20" width="70" height="60" rx="8" fill="#8B4513"/>
									<rect x="18" y="23" width="64" height="54" rx="6" fill="#A0522D"/>

									<!-- Screen -->
									<rect x="23" y="28" width="54" height="38" rx="3" fill="#2D4F67"/>
									<rect x="25" y="30" width="50" height="34" rx="2" fill="#4A90B5" opacity="0.6"/>

									<!-- Control Panel -->
									<circle cx="72" cy="72" r="3" fill="#654321"/>
									<circle cx="65" cy="72" r="2.5" fill="#654321"/>
									<circle cx="58" cy="72" r="2" fill="#654321"/>

									<!-- Speaker grille -->
									<line x1="28" y1="72" x2="48" y2="72" stroke="#654321" stroke-width="1"/>
									<line x1="28" y1="75" x2="48" y2="75" stroke="#654321" stroke-width="1"/>

									<!-- TV Legs -->
									<rect x="28" y="80" width="8" height="10" rx="2" fill="#8B4513"/>
									<rect x="64" y="80" width="8" height="10" rx="2" fill="#8B4513"/>
								</svg>
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
						</div>
					</div>

					<div class="hidden sm:ml-6 sm:flex sm:items-center">
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
