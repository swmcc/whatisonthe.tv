<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';

	const dispatch = createEventDispatcher();

	export let checkins: any[] = [];
	export let filterInfo: { startDate: string; endDate: string } | null = null;

	let userPrompt = '';

	function handleSubmit() {
		if (!userPrompt.trim()) return;

		// Store context and navigate - streaming happens on /swanson page
		if (browser) {
			const searchResults = checkins.map(checkin => ({
				id: checkin.content?.tvdb_id || checkin.content?.id,
				name: checkin.content?.name || 'Unknown',
				type: checkin.content?.content_type || 'unknown',
				year: checkin.content?.year,
				genres: []
			}));

			sessionStorage.setItem('swanson_checkins', JSON.stringify(checkins));
			sessionStorage.setItem('swanson_filter', JSON.stringify(filterInfo || {}));
			sessionStorage.setItem('swanson_pending_prompt', userPrompt);
			sessionStorage.setItem('swanson_search_results', JSON.stringify(searchResults));
		}

		goto('/swanson');
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit();
		}
		if (e.key === 'Escape') {
			close();
		}
	}

	function close() {
		dispatch('close');
	}
</script>

<!-- Modal Backdrop -->
<div
	class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
	on:click={close}
	on:keydown={(e) => e.key === 'Escape' && close()}
	role="dialog"
	tabindex="-1"
>
	<!-- Modal Content -->
	<div
		class="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden"
		on:click|stopPropagation
		on:keydown|stopPropagation
		role="document"
	>
		<!-- Header -->
		<div class="bg-gradient-to-r from-indigo-600 to-indigo-800 px-6 py-5">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-4">
					<img
						src="/swanson.png"
						alt="Swanson"
						class="w-16 h-16 rounded-full object-cover border-4 border-white shadow-lg"
					/>
					<div>
						<h2 class="text-xl font-bold text-white">Swanson</h2>
						<p class="text-indigo-200 text-sm">
							{checkins.length} check-ins loaded
						</p>
					</div>
				</div>
				<button
					on:click={close}
					class="text-white/70 hover:text-white transition-colors"
					aria-label="Close"
				>
					<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
		</div>

		<!-- Body -->
		<div class="p-6">
			<div class="space-y-4">
				<div>
					<label for="prompt" class="block text-sm font-medium text-gray-700 mb-2">
						What are you in the mood for?
					</label>
					<textarea
						id="prompt"
						bind:value={userPrompt}
						on:keydown={handleKeydown}
						placeholder="Something like Breaking Bad but funnier..."
						rows="3"
						class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
					/>
				</div>

				<button
					on:click={handleSubmit}
					disabled={!userPrompt.trim()}
					class="w-full px-4 py-3 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
				>
					Ask Swanson
				</button>
			</div>
		</div>
	</div>
</div>
