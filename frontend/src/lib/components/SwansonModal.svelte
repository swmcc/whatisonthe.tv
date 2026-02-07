<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { api } from '$lib/api';

	const dispatch = createEventDispatcher();

	export let checkins: any[] = [];
	export let testMode = false; // Set to true to test loading state without API call

	// Ron Swanson quotes for the loading state
	const SWANSON_QUOTES = [
		"Never half-ass two things. Whole-ass one thing.",
		"Give a man a fish and feed him for a day. Don't teach a man to fish... and feed yourself. He's a grown man. Fishing's not that hard.",
		"There's only one thing I hate more than lying: skim milk. Which is water that's lying about being milk.",
		"Crying: acceptable at funerals and the Grand Canyon.",
		"Clear alcohols are for rich women on diets.",
		"I'm a simple man. I like pretty, dark-haired women and breakfast food.",
		"Any dog under 50 pounds is a cat and cats are useless.",
		"History began July 4th, 1776. Everything before that was a mistake.",
		"There is only one bad word: taxes.",
		"I'd wish you the best of luck but I believe luck is a concept created by the weak to explain their failures.",
		"The less I know about other people's affairs, the happier I am.",
		"When people get too chummy with me, I like to call them by the wrong name to let them know I don't really care about them.",
		"I once worked with a guy for three years and never learned his name. Best friend I ever had.",
		"Just give me all the bacon and eggs you have.",
		"Fishing relaxes me. It's like yoga, except I still get to kill something."
	];

	let userPrompt = '';
	let loading = false;
	let response = '';
	let error = '';
	let currentQuote = '';
	let quoteInterval: ReturnType<typeof setInterval>;
	let spinAngle = 0;
	let spinInterval: ReturnType<typeof setInterval>;

	// Initialize with a random quote
	currentQuote = getRandomQuote();

	function getRandomQuote(): string {
		return SWANSON_QUOTES[Math.floor(Math.random() * SWANSON_QUOTES.length)];
	}

	function startLoadingAnimation() {
		currentQuote = getRandomQuote();
		// Rotate quotes every 3 seconds
		quoteInterval = setInterval(() => {
			currentQuote = getRandomQuote();
		}, 3000);
		// Spin the head
		spinInterval = setInterval(() => {
			spinAngle = (spinAngle + 5) % 360;
		}, 50);
	}

	function stopLoadingAnimation() {
		if (quoteInterval) clearInterval(quoteInterval);
		if (spinInterval) clearInterval(spinInterval);
		spinAngle = 0;
	}

	async function handleSubmit() {
		if (!userPrompt.trim()) return;

		loading = true;
		error = '';
		response = '';
		startLoadingAnimation();

		try {
			if (testMode) {
				// Test mode - just wait 5 seconds to see the loading state
				await new Promise(resolve => setTimeout(resolve, 5000));
				response = "This is a test response. In production, Swanson would give you real recommendations based on your viewing history.";
			} else {
				// Real API call
				const searchResults = checkins.map(checkin => ({
					id: checkin.content?.tvdb_id || checkin.content?.id,
					name: checkin.content?.name || 'Unknown',
					type: checkin.content?.content_type || 'unknown',
					year: checkin.content?.year,
					genres: []
				}));

				const result = await api.swanson.recommend({
					prompt: userPrompt,
					search_results: searchResults
				});
				response = result.recommendation;
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to get recommendation';
		} finally {
			loading = false;
			stopLoadingAnimation();
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit();
		}
		if (e.key === 'Escape' && !loading) {
			close();
		}
	}

	function close() {
		if (!loading) {
			dispatch('close');
		}
	}

	function reset() {
		response = '';
		error = '';
		userPrompt = '';
	}
</script>

<!-- Modal Backdrop -->
<div
	class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
	on:click={close}
	on:keydown={(e) => e.key === 'Escape' && !loading && close()}
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
					<div
						class="relative"
						style="transform: rotate({spinAngle}deg); transition: transform 0.05s linear;"
					>
						<img
							src="/swanson.png"
							alt="Swanson"
							class="w-16 h-16 rounded-full object-cover border-3 border-white shadow-lg"
							class:animate-pulse={loading}
						/>
					</div>
					<div>
						<h2 class="text-xl font-bold text-white">Swanson</h2>
						<p class="text-indigo-200 text-sm">
							{#if loading}
								Thinking...
							{:else}
								{checkins.length} check-ins loaded
							{/if}
						</p>
					</div>
				</div>
				{#if !loading}
					<button
						on:click={close}
						class="text-white/70 hover:text-white transition-colors"
						aria-label="Close"
					>
						<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				{/if}
			</div>
		</div>

		<!-- Body -->
		<div class="p-6">
			{#if loading}
				<!-- Loading State -->
				<div class="text-center py-8">
					<div class="mb-6">
						<svg
							class="animate-spin h-10 w-10 text-indigo-600 mx-auto"
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
					</div>
					<p class="text-lg text-gray-700 italic max-w-sm mx-auto leading-relaxed">
						"{currentQuote}"
					</p>
					<p class="text-xs text-gray-400 mt-4">- Ron Swanson</p>
				</div>
			{:else if response}
				<!-- Response -->
				<div class="space-y-4">
					<div class="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
						<p class="text-gray-800 whitespace-pre-wrap">{response}</p>
					</div>

					<div class="flex gap-3">
						<button
							on:click={reset}
							class="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
						>
							Ask Another
						</button>
						<button
							on:click={close}
							class="flex-1 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
						>
							Done
						</button>
					</div>
				</div>
			{:else}
				<!-- Input State -->
				<div class="space-y-4">
					{#if error}
						<div class="p-3 bg-red-50 border-l-4 border-red-400 text-red-700 text-sm rounded">
							{error}
						</div>
					{/if}

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

					{#if testMode}
						<p class="text-xs text-center text-amber-600">
							Test mode enabled - will simulate 5 second delay
						</p>
					{/if}
				</div>
			{/if}
		</div>
	</div>
</div>
