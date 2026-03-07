<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { api } from '$lib/api';

	export let type: 'content' | 'person';
	export let id: number; // TVDB ID for content, person ID for person
	export let personRoleFilter: 'any' | 'actor' | 'director' = 'any';
	export let compact: boolean = false;

	const dispatch = createEventDispatcher();

	let inWatchlist = false;
	let loading = false;
	let checking = true;

	onMount(async () => {
		await checkWatchlistStatus();
	});

	async function checkWatchlistStatus() {
		checking = true;
		try {
			const response =
				type === 'content'
					? await api.watchlist.checkContent(id)
					: await api.watchlist.checkPerson(id);
			inWatchlist = response.in_watchlist;
		} catch (e) {
			console.error('Failed to check watchlist status:', e);
		} finally {
			checking = false;
		}
	}

	async function toggleWatchlist() {
		if (loading) return;

		loading = true;
		try {
			if (inWatchlist) {
				// Remove from watchlist
				if (type === 'content') {
					await api.watchlist.removeContent(id);
				} else {
					await api.watchlist.removePerson(id);
				}
				inWatchlist = false;
				dispatch('removed', { type, id });
			} else {
				// Add to watchlist
				if (type === 'content') {
					await api.watchlist.addContent(id);
				} else {
					await api.watchlist.addPerson(id, personRoleFilter);
				}
				inWatchlist = true;
				dispatch('added', { type, id });
			}
		} catch (e: any) {
			console.error('Failed to update watchlist:', e);
			// Handle 409 conflict (already in watchlist)
			if (e.message?.includes('already in watchlist')) {
				inWatchlist = true;
			}
		} finally {
			loading = false;
		}
	}
</script>

{#if checking}
	<button
		disabled
		class="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed
			{compact ? 'px-3 py-1.5 text-sm' : ''}"
	>
		<svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
			<circle
				class="opacity-25"
				cx="12"
				cy="12"
				r="10"
				stroke="currentColor"
				stroke-width="4"
				fill="none"
			></circle>
			<path
				class="opacity-75"
				fill="currentColor"
				d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
			></path>
		</svg>
		{#if !compact}
			<span>Loading...</span>
		{/if}
	</button>
{:else}
	<button
		on:click={toggleWatchlist}
		disabled={loading}
		class="flex items-center gap-2 rounded-lg border font-medium transition-all focus:outline-none focus:ring-2 focus:ring-offset-2
			{compact ? 'px-3 py-1.5 text-sm' : 'px-4 py-2'}
			{inWatchlist
			? 'border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100 focus:ring-amber-500'
			: 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:ring-indigo-500'}
			{loading ? 'opacity-75 cursor-not-allowed' : ''}"
		title={inWatchlist ? 'Remove from watchlist' : 'Add to watchlist'}
	>
		{#if loading}
			<svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
				<circle
					class="opacity-25"
					cx="12"
					cy="12"
					r="10"
					stroke="currentColor"
					stroke-width="4"
					fill="none"
				></circle>
				<path
					class="opacity-75"
					fill="currentColor"
					d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
				></path>
			</svg>
		{:else}
			<!-- Bookmark icon -->
			<svg
				class="h-5 w-5 {compact ? 'h-4 w-4' : ''}"
				fill={inWatchlist ? 'currentColor' : 'none'}
				viewBox="0 0 24 24"
				stroke="currentColor"
				stroke-width="2"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
				/>
			</svg>
		{/if}
		{#if !compact}
			<span>{inWatchlist ? 'In Watchlist' : 'Add to Watchlist'}</span>
		{/if}
	</button>
{/if}
