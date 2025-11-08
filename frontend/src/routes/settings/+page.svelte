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

	$: if ($auth.user) {
		user = $auth.user;
		firstName = user.first_name;
		lastName = user.last_name;
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

<div class="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900">Settings</h1>
		<p class="mt-2 text-gray-600">Manage your account settings and preferences</p>
	</div>

		<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
			<!-- Profile Settings -->
			<div class="bg-white rounded-lg shadow p-6">
				<h2 class="text-xl font-semibold text-gray-900 mb-6">Profile Information</h2>

				<form on:submit|preventDefault={handleProfileUpdate} class="space-y-6">
					{#if profileSuccess}
						<div class="bg-green-50 border-l-4 border-green-500 p-4 rounded">
							<p class="text-sm text-green-700">{profileSuccess}</p>
						</div>
					{/if}

					{#if profileError}
						<div class="bg-red-50 border-l-4 border-red-500 p-4 rounded">
							<p class="text-sm text-red-700">{profileError}</p>
						</div>
					{/if}

					<div>
						<label for="email" class="block text-sm font-medium text-gray-700 mb-2">
							Email Address
						</label>
						<input
							id="email"
							type="email"
							value={user?.email || ''}
							disabled
							class="block w-full px-4 py-2 rounded-lg border border-gray-300 bg-gray-50 text-gray-500 cursor-not-allowed"
						/>
						<p class="mt-1 text-xs text-gray-500">Email cannot be changed</p>
					</div>

					<div>
						<label for="firstName" class="block text-sm font-medium text-gray-700 mb-2">
							First Name
						</label>
						<input
							id="firstName"
							type="text"
							bind:value={firstName}
							required
							class="block w-full px-4 py-2 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
						/>
					</div>

					<div>
						<label for="lastName" class="block text-sm font-medium text-gray-700 mb-2">
							Last Name
						</label>
						<input
							id="lastName"
							type="text"
							bind:value={lastName}
							required
							class="block w-full px-4 py-2 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
						/>
					</div>

					<button
						type="submit"
						disabled={loadingProfile}
						class="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{loadingProfile ? 'Updating...' : 'Update Profile'}
					</button>
				</form>
			</div>

			<!-- Password Settings -->
			<div class="bg-white rounded-lg shadow p-6">
				<h2 class="text-xl font-semibold text-gray-900 mb-6">Change Password</h2>

				<form on:submit|preventDefault={handlePasswordUpdate} class="space-y-6">
					{#if passwordSuccess}
						<div class="bg-green-50 border-l-4 border-green-500 p-4 rounded">
							<p class="text-sm text-green-700">{passwordSuccess}</p>
						</div>
					{/if}

					{#if passwordError}
						<div class="bg-red-50 border-l-4 border-red-500 p-4 rounded">
							<p class="text-sm text-red-700">{passwordError}</p>
						</div>
					{/if}

					<div>
						<label for="currentPassword" class="block text-sm font-medium text-gray-700 mb-2">
							Current Password
						</label>
						<input
							id="currentPassword"
							type="password"
							bind:value={currentPassword}
							required
							autocomplete="current-password"
							class="block w-full px-4 py-2 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
						/>
					</div>

					<div>
						<label for="newPassword" class="block text-sm font-medium text-gray-700 mb-2">
							New Password
						</label>
						<input
							id="newPassword"
							type="password"
							bind:value={newPassword}
							required
							autocomplete="new-password"
							class="block w-full px-4 py-2 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
						/>
					</div>

					<div>
						<label for="confirmPassword" class="block text-sm font-medium text-gray-700 mb-2">
							Confirm New Password
						</label>
						<input
							id="confirmPassword"
							type="password"
							bind:value={confirmPassword}
							required
							autocomplete="new-password"
							class="block w-full px-4 py-2 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
						/>
					</div>

					<button
						type="submit"
						disabled={loadingPassword}
						class="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{loadingPassword ? 'Updating...' : 'Change Password'}
					</button>
				</form>
			</div>
		</div>
</div>
