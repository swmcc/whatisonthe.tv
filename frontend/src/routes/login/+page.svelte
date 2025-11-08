<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { auth } from '$lib/stores/auth';

	let email = '';
	let password = '';
	let error = '';
	let loading = false;

	async function handleSubmit() {
		error = '';
		loading = true;

		try {
			const response = await api.auth.login(email, password);
			auth.login(response.user, response.access_token);
			goto('/');
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Login - What Is On The TV</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
	<div class="max-w-md w-full">
		<div class="bg-white rounded-2xl shadow-xl p-8">
			<div class="text-center mb-8">
				<h1 class="text-3xl font-bold text-gray-900 mb-2">Welcome Back</h1>
				<p class="text-gray-600">Sign in to continue to What Is On The TV</p>
			</div>

			<form on:submit|preventDefault={handleSubmit} class="space-y-6">
				{#if error}
					<div class="bg-red-50 border-l-4 border-red-500 p-4 rounded">
						<div class="flex">
							<div class="flex-shrink-0">
								<svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
									<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
								</svg>
							</div>
							<div class="ml-3">
								<p class="text-sm text-red-700">{error}</p>
							</div>
						</div>
					</div>
				{/if}

				<div>
					<label for="email" class="block text-sm font-medium text-gray-700 mb-2">
						Email Address
					</label>
					<input
						id="email"
						type="email"
						bind:value={email}
						required
						autocomplete="email"
						class="block w-full px-4 py-3 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
						placeholder="you@example.com"
					/>
				</div>

				<div>
					<label for="password" class="block text-sm font-medium text-gray-700 mb-2">
						Password
					</label>
					<input
						id="password"
						type="password"
						bind:value={password}
						required
						autocomplete="current-password"
						class="block w-full px-4 py-3 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
						placeholder="••••••••"
					/>
				</div>

				<button
					type="submit"
					disabled={loading}
					class="w-full flex justify-center items-center px-4 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{#if loading}
						<svg class="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						Signing in...
					{:else}
						Sign In
					{/if}
				</button>
			</form>
		</div>

		<p class="mt-6 text-center text-sm text-gray-600">
			Secure login powered by What Is On The TV
		</p>
	</div>
</div>
