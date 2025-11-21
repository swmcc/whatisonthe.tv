<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { auth } from '$lib/stores/auth';

	let user: any = null;
	let firstName = '';
	let lastName = '';
	let currentPassword = '';
	let newPassword = '';
	let confirmPassword = '';

	let profileError = '';
	let profileSuccess = '';
	let passwordError = '';
	let passwordSuccess = '';
	let loadingProfile = false;
	let loadingPassword = false;

	// Tab management
	let activeTab: 'profile' | 'security' = 'profile';

	$: if ($auth.user) {
		user = $auth.user;
		firstName = user.first_name || '';
		lastName = user.last_name || '';
	}

	async function handleProfileUpdate() {
		profileError = '';
		profileSuccess = '';
		loadingProfile = true;

		try {
			const updated = await api.auth.updateProfile({
				first_name: firstName,
				last_name: lastName
			});
			auth.setUser(updated);
			profileSuccess = 'Profile updated successfully!';
			setTimeout(() => {
				profileSuccess = '';
			}, 3000);
		} catch (err) {
			profileError = err instanceof Error ? err.message : 'Failed to update profile';
		} finally {
			loadingProfile = false;
		}
	}

	async function handlePasswordUpdate() {
		passwordError = '';
		passwordSuccess = '';

		if (newPassword !== confirmPassword) {
			passwordError = 'New passwords do not match';
			return;
		}

		if (newPassword.length < 6) {
			passwordError = 'Password must be at least 6 characters';
			return;
		}

		loadingPassword = true;

		try {
			await api.auth.updatePassword(currentPassword, newPassword);
			passwordSuccess = 'Password updated successfully!';
			currentPassword = '';
			newPassword = '';
			confirmPassword = '';
			setTimeout(() => {
				passwordSuccess = '';
			}, 3000);
		} catch (err) {
			passwordError = err instanceof Error ? err.message : 'Failed to update password';
		} finally {
			loadingPassword = false;
		}
	}
</script>

<svelte:head>
	<title>Settings - What Is On The TV</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 py-8">
	<div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
		<!-- Header -->
		<div class="mb-8">
			<h1 class="text-4xl font-bold text-gray-900">Account Settings</h1>
			<p class="mt-3 text-lg text-gray-600">Manage your profile information and security settings</p>
		</div>

		<!-- Tabs Container -->
		<div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
			<!-- Tab Navigation -->
			<div class="border-b border-gray-200">
				<nav class="flex -mb-px">
					<button
						on:click={() => activeTab = 'profile'}
						class="flex-1 py-4 px-6 text-center border-b-2 font-medium text-sm transition-all {activeTab === 'profile'
							? 'border-indigo-600 text-indigo-600 bg-indigo-50'
							: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
					>
						<span class="flex items-center justify-center gap-2">
							<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
							</svg>
							Profile
						</span>
					</button>
					<button
						on:click={() => activeTab = 'security'}
						class="flex-1 py-4 px-6 text-center border-b-2 font-medium text-sm transition-all {activeTab === 'security'
							? 'border-purple-600 text-purple-600 bg-purple-50'
							: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
					>
						<span class="flex items-center justify-center gap-2">
							<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
							</svg>
							Security
						</span>
					</button>
				</nav>
			</div>

			<!-- Tab Content -->
			{#if activeTab === 'profile'}
				<!-- Profile Tab -->
				<form on:submit|preventDefault={handleProfileUpdate} class="p-8 space-y-6">
					<div class="mb-6">
						<h2 class="text-2xl font-semibold text-gray-900">Profile Information</h2>
						<p class="mt-1 text-sm text-gray-600">Update your personal details</p>
					</div>

					{#if profileSuccess}
						<div class="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
							<svg class="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
							</svg>
							<p class="text-sm font-medium text-green-800">{profileSuccess}</p>
						</div>
					{/if}

					{#if profileError}
						<div class="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
							<svg class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
							</svg>
							<p class="text-sm font-medium text-red-800">{profileError}</p>
						</div>
					{/if}

					<div>
						<label for="email" class="block text-sm font-semibold text-gray-700 mb-2">
							Email Address
						</label>
						<div class="relative">
							<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
								<svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
								</svg>
							</div>
							<input
								id="email"
								type="email"
								value={user?.email || ''}
								disabled
								class="block w-full pl-10 pr-3 py-2.5 rounded-lg border border-gray-300 bg-gray-50 text-gray-500 cursor-not-allowed text-sm"
							/>
						</div>
						<p class="mt-1.5 text-xs text-gray-500 flex items-center gap-1">
							<svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
							</svg>
							Email address cannot be changed
						</p>
					</div>

					<div>
						<label for="firstName" class="block text-sm font-semibold text-gray-700 mb-2">
							First Name
						</label>
						<input
							id="firstName"
							type="text"
							bind:value={firstName}
							placeholder="Enter your first name"
							class="block w-full px-4 py-2.5 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all text-sm placeholder-gray-400"
						/>
					</div>

					<div>
						<label for="lastName" class="block text-sm font-semibold text-gray-700 mb-2">
							Last Name
						</label>
						<input
							id="lastName"
							type="text"
							bind:value={lastName}
							placeholder="Enter your last name"
							class="block w-full px-4 py-2.5 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all text-sm placeholder-gray-400"
						/>
					</div>

					<button
						type="submit"
						disabled={loadingProfile}
						class="w-full px-4 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium rounded-lg hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
					>
						{#if loadingProfile}
							<span class="flex items-center justify-center gap-2">
								<svg class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
								</svg>
								Updating...
							</span>
						{:else}
							Save Changes
						{/if}
					</button>
				</form>
			{:else if activeTab === 'security'}
				<!-- Security Tab -->
				<form on:submit|preventDefault={handlePasswordUpdate} class="p-8 space-y-6">
					<div class="mb-6">
						<h2 class="text-2xl font-semibold text-gray-900">Security</h2>
						<p class="mt-1 text-sm text-gray-600">Change your password</p>
					</div>

					{#if passwordSuccess}
						<div class="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
							<svg class="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
							</svg>
							<p class="text-sm font-medium text-green-800">{passwordSuccess}</p>
						</div>
					{/if}

					{#if passwordError}
						<div class="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
							<svg class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
							</svg>
							<p class="text-sm font-medium text-red-800">{passwordError}</p>
						</div>
					{/if}

					<div>
						<label for="currentPassword" class="block text-sm font-semibold text-gray-700 mb-2">
							Current Password
						</label>
						<input
							id="currentPassword"
							type="password"
							bind:value={currentPassword}
							required
							autocomplete="current-password"
							placeholder="Enter current password"
							class="block w-full px-4 py-2.5 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all text-sm placeholder-gray-400"
						/>
					</div>

					<div>
						<label for="newPassword" class="block text-sm font-semibold text-gray-700 mb-2">
							New Password
						</label>
						<input
							id="newPassword"
							type="password"
							bind:value={newPassword}
							required
							autocomplete="new-password"
							placeholder="Enter new password"
							class="block w-full px-4 py-2.5 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all text-sm placeholder-gray-400"
						/>
						<p class="mt-1.5 text-xs text-gray-500">Minimum 6 characters required</p>
					</div>

					<div>
						<label for="confirmPassword" class="block text-sm font-semibold text-gray-700 mb-2">
							Confirm New Password
						</label>
						<input
							id="confirmPassword"
							type="password"
							bind:value={confirmPassword}
							required
							autocomplete="new-password"
							placeholder="Confirm new password"
							class="block w-full px-4 py-2.5 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all text-sm placeholder-gray-400"
						/>
					</div>

					<button
						type="submit"
						disabled={loadingPassword}
						class="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium rounded-lg hover:from-purple-700 hover:to-pink-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
					>
						{#if loadingPassword}
							<span class="flex items-center justify-center gap-2">
								<svg class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
								</svg>
								Updating...
							</span>
						{:else}
							Update Password
						{/if}
					</button>
				</form>
			{/if}
		</div>
	</div>
</div>
