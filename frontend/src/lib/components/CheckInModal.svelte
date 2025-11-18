<script lang="ts">
	import { api } from '$lib/api';
	import { createEventDispatcher } from 'svelte';

	export let contentId: number;
	export let contentName: string;
	export let contentType: 'series' | 'movie';
	export let episodeId: number | null = null;
	export let episodeName: string | null = null;
	export let seasonNumber: number | null = null;
	export let episodeNumber: number | null = null;

	const dispatch = createEventDispatcher();

	let watchedAt = new Date().toISOString().slice(0, 16);
	let location = '';
	let watchedWith = '';
	let notes = '';
	let loading = false;
	let error = '';
	let success = false;

	function formatEpisode() {
		if (seasonNumber !== null && episodeNumber !== null) {
			return `S${seasonNumber.toString().padStart(2, '0')}E${episodeNumber.toString().padStart(2, '0')}`;
		}
		return '';
	}

	async function handleSubmit() {
		loading = true;
		error = '';
		success = false;

		try {
			await api.checkin.create({
				content_id: contentId,
				episode_id: episodeId || undefined,
				watched_at: new Date(watchedAt).toISOString(),
				location: location || undefined,
				watched_with: watchedWith || undefined,
				notes: notes || undefined
			});

			success = true;
			setTimeout(() => {
				dispatch('success');
				close();
			}, 1000);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create check-in';
		} finally {
			loading = false;
		}
	}

	function close() {
		dispatch('close');
	}
</script>

<div
	class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center"
	on:click={close}
	on:keydown={(e) => e.key === 'Escape' && close()}
	role="button"
	tabindex="0"
>
	<div
		class="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4"
		on:click|stopPropagation
		on:keydown|stopPropagation
		role="dialog"
		tabindex="-1"
	>
		<!-- Header -->
		<div class="px-6 py-4 border-b border-gray-200">
			<div class="flex items-center justify-between">
				<h3 class="text-lg font-semibold text-gray-900">Check In</h3>
				<button
					on:click={close}
					class="text-gray-400 hover:text-gray-500 focus:outline-none"
					type="button"
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>
		</div>

		<!-- Body -->
		<form on:submit|preventDefault={handleSubmit} class="px-6 py-4">
			{#if error}
				<div class="mb-4 p-3 bg-red-50 border-l-4 border-red-400 text-red-700 text-sm">
					{error}
				</div>
			{/if}

			{#if success}
				<div class="mb-4 p-3 bg-green-50 border-l-4 border-green-400 text-green-700 text-sm">
					Check-in created successfully!
				</div>
			{/if}

			<!-- Content Info -->
			<div class="mb-4 p-3 bg-indigo-50 rounded-md">
				<p class="text-sm font-medium text-indigo-900">{contentName}</p>
				{#if episodeId && episodeName}
					<p class="text-xs text-indigo-700 mt-1">
						{formatEpisode()}
						{#if episodeName}
							- {episodeName}
						{/if}
					</p>
				{/if}
			</div>

			<!-- Watched At -->
			<div class="mb-4">
				<label for="watchedAt" class="block text-sm font-medium text-gray-700 mb-1">
					When did you watch this? <span class="text-red-500">*</span>
				</label>
				<input
					type="datetime-local"
					id="watchedAt"
					bind:value={watchedAt}
					required
					class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
				/>
			</div>

			<!-- Location -->
			<div class="mb-4">
				<label for="location" class="block text-sm font-medium text-gray-700 mb-1">
					Where?
				</label>
				<input
					type="text"
					id="location"
					bind:value={location}
					placeholder="e.g., Home, Cinema, Friend's house"
					maxlength="255"
					class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
				/>
			</div>

			<!-- Watched With -->
			<div class="mb-4">
				<label for="watchedWith" class="block text-sm font-medium text-gray-700 mb-1">
					Who with?
				</label>
				<input
					type="text"
					id="watchedWith"
					bind:value={watchedWith}
					placeholder="e.g., Friends, Family, Alone"
					maxlength="255"
					class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
				/>
			</div>

			<!-- Notes -->
			<div class="mb-4">
				<label for="notes" class="block text-sm font-medium text-gray-700 mb-1"> Notes </label>
				<textarea
					id="notes"
					bind:value={notes}
					rows="3"
					placeholder="Any thoughts or comments?"
					class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
				/>
			</div>

			<!-- Footer -->
			<div class="flex gap-3 justify-end mt-6">
				<button
					type="button"
					on:click={close}
					class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
					disabled={loading}
				>
					Cancel
				</button>
				<button
					type="submit"
					class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
					disabled={loading}
				>
					{#if loading}
						<svg
							class="animate-spin h-4 w-4 inline-block mr-2"
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
						>
							<circle
								class="opacity-25"
								cx="12"
								cy="12"
								r="10"
								stroke="currentColor"
								stroke-width="4"
							/>
							<path
								class="opacity-75"
								fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
							/>
						</svg>
						Saving...
					{:else}
						Check In
					{/if}
				</button>
			</div>
		</form>
	</div>
</div>
