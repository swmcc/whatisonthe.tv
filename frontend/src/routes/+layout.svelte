<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';
	import { api } from '$lib/api';

	let menuOpen = false;

	// Check authentication on mount
	onMount(async () => {
		if ($auth.token && !$auth.user) {
			try {
				const user = await api.auth.me();
				auth.setUser(user);
			} catch (err) {
				// Don't logout on errors - the api.ts will handle invalid tokens
				// This prevents logout on network errors or server restarts
				console.error('Failed to fetch user info:', err);
			}
		}

		// Redirect to login if not authenticated (except on login page)
		if (!$auth.token && $page.url.pathname !== '/login') {
			goto('/login');
		}
	});

	// Reactive: redirect to home if authenticated and on login page
	$: if ($auth.token && $page.url.pathname === '/login') {
		goto('/');
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
							<a href="/" class="text-xl font-bold text-indigo-600">
								What Is On The TV
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
								href="/settings"
								class="border-transparent text-gray-500 hover:text-gray-900 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium hover:border-indigo-500 transition-colors"
								class:border-indigo-500={$page.url.pathname === '/settings'}
								class:text-indigo-600={$page.url.pathname === '/settings'}
							>
								Settings
							</a>
						</div>
					</div>

					<div class="hidden sm:ml-6 sm:flex sm:items-center">
						<div class="relative">
							<button
								on:click={() => menuOpen = !menuOpen}
								class="flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
							>
								<span class="sr-only">Open user menu</span>
								<div class="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center text-white font-medium">
									{$auth.user.first_name[0]}{$auth.user.last_name[0]}
								</div>
								<span class="ml-3 text-gray-700 font-medium">
									{$auth.user.first_name} {$auth.user.last_name}
								</span>
								<svg class="ml-2 h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
									<path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
								</svg>
							</button>

							{#if menuOpen}
								<div class="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-10">
									<div class="py-1">
										<button
											on:click={handleLogout}
											class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
										>
											Sign Out
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
							href="/settings"
							class="block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
							class:border-indigo-500={$page.url.pathname === '/settings'}
							class:bg-indigo-50={$page.url.pathname === '/settings'}
							class:text-indigo-700={$page.url.pathname === '/settings'}
							class:border-transparent={$page.url.pathname !== '/settings'}
							class:text-gray-600={$page.url.pathname !== '/settings'}
						>
							Settings
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
							<button
								on:click={handleLogout}
								class="block w-full text-left px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
							>
								Sign Out
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
	</div>
{:else}
	<!-- Loading state -->
	<div class="min-h-screen bg-gray-50 flex items-center justify-center">
		<div class="text-center">
			<svg class="animate-spin h-12 w-12 text-indigo-600 mx-auto" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
			</svg>
			<p class="mt-4 text-gray-600">Loading...</p>
		</div>
	</div>
{/if}
