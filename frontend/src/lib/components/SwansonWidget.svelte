<script lang="ts">
	import { api } from '$lib/api';

	let isOpen = false;
	let userPrompt = '';
	let loading = false;
	let response = '';
	let error = '';

	// Props for context (search results, etc.)
	export let searchResults: Array<{
		id: number;
		name: string;
		type: string;
		year?: number;
		genres?: string[];
	}> = [];

	function toggle() {
		isOpen = !isOpen;
		if (!isOpen) {
			// Reset state when closing
			response = '';
			error = '';
		}
	}

	function close() {
		isOpen = false;
		response = '';
		error = '';
	}

	async function handleSubmit() {
		if (!userPrompt.trim()) return;

		loading = true;
		error = '';
		response = '';

		try {
			const result = await api.swanson.recommend({
				prompt: userPrompt,
				search_results: searchResults
			});
			response = result.recommendation;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to get recommendation';
		} finally {
			loading = false;
		}
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
</script>

<!-- Floating Swanson Button -->
<div class="fixed bottom-6 right-6 z-50">
	{#if isOpen}
		<!-- Popup Panel -->
		<div
			class="absolute bottom-20 right-0 w-80 bg-white rounded-lg shadow-2xl border border-gray-200 overflow-hidden"
		>
			<!-- Header -->
			<div class="bg-indigo-600 px-4 py-3 flex items-center justify-between">
				<div class="flex items-center gap-2">
					<img
						src="/swanson.png"
						alt="Swanson"
						class="w-8 h-8 rounded-full object-cover bg-white"
					/>
					<span class="text-white font-medium">Swanson</span>
				</div>
				<button
					on:click={close}
					class="text-white/80 hover:text-white focus:outline-none"
					type="button"
					aria-label="Close"
				>
					<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>

			<!-- Body -->
			<div class="p-4">
				{#if error}
					<div class="mb-3 p-2 bg-red-50 border-l-4 border-red-400 text-red-700 text-sm">
						{error}
					</div>
				{/if}

				{#if response}
					<div class="mb-3 p-3 bg-gray-50 rounded-md text-sm text-gray-700 max-h-48 overflow-y-auto">
						{response}
					</div>
				{/if}

				<div class="space-y-3">
					<textarea
						bind:value={userPrompt}
						on:keydown={handleKeydown}
						placeholder="What are you in the mood for?"
						rows="3"
						disabled={loading}
						class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-sm resize-none disabled:bg-gray-100"
					/>

					<button
						on:click={handleSubmit}
						disabled={loading || !userPrompt.trim()}
						class="w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
					>
						{#if loading}
							<svg
								class="animate-spin h-4 w-4"
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
							Thinking...
						{:else}
							Ask Swanson
						{/if}
					</button>
				</div>

				{#if searchResults.length > 0}
					<p class="mt-2 text-xs text-gray-500 text-center">
						Considering {searchResults.length} search results
					</p>
				{/if}
			</div>
		</div>
	{/if}

	<!-- Toggle Button -->
	<button
		on:click={toggle}
		class="w-16 h-16 rounded-full shadow-lg hover:shadow-xl transition-shadow duration-200 overflow-hidden border-2 border-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
		aria-label={isOpen ? 'Close Swanson' : 'Ask Swanson for recommendations'}
	>
		<img src="/swanson.png" alt="Swanson" class="w-full h-full object-cover" />
	</button>
</div>
