<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { api } from '$lib/api';

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
	let checkinData: any[] = [];
	let hasDateFilter = false;

	onMount(() => {
		// Get checkin data from sessionStorage
		if (browser) {
			const stored = sessionStorage.getItem('swanson_checkins');
			const filterInfo = sessionStorage.getItem('swanson_filter');

			if (stored) {
				checkinData = JSON.parse(stored);
			}
			if (filterInfo) {
				hasDateFilter = JSON.parse(filterInfo).hasDateFilter;
			}

			// If no date filter, redirect back with message
			if (!hasDateFilter) {
				error = "That's too much data. Please filter your checkins by date first.";
			}
		}

		// Set initial quote
		currentQuote = getRandomQuote();

		return () => {
			if (quoteInterval) clearInterval(quoteInterval);
		};
	});

	function getRandomQuote(): string {
		return SWANSON_QUOTES[Math.floor(Math.random() * SWANSON_QUOTES.length)];
	}

	function startQuoteRotation() {
		currentQuote = getRandomQuote();
		quoteInterval = setInterval(() => {
			currentQuote = getRandomQuote();
		}, 4000);
	}

	function stopQuoteRotation() {
		if (quoteInterval) {
			clearInterval(quoteInterval);
		}
	}

	async function handleSubmit() {
		if (!userPrompt.trim()) return;
		if (!hasDateFilter) {
			error = "That's too much data. Please filter your checkins by date first.";
			return;
		}

		loading = true;
		error = '';
		response = '';
		startQuoteRotation();

		try {
			// Transform checkin data to search results format
			const searchResults = checkinData.map(checkin => ({
				id: checkin.content?.tvdb_id || checkin.content?.id,
				name: checkin.content?.name || 'Unknown',
				type: checkin.content?.content_type || 'unknown',
				year: checkin.content?.year,
				genres: [] // Could be populated if available
			}));

			const result = await api.swanson.recommend({
				prompt: userPrompt,
				search_results: searchResults
			});
			response = result.recommendation;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to get recommendation';
		} finally {
			loading = false;
			stopQuoteRotation();
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit();
		}
	}

	function goBack() {
		goto('/checkins');
	}
</script>

<div class="min-h-screen bg-gray-50 py-12">
	<div class="max-w-2xl mx-auto px-4">
		<!-- Header with back button -->
		<div class="mb-8">
			<button
				on:click={goBack}
				class="text-gray-600 hover:text-gray-900 flex items-center gap-2 mb-4"
			>
				<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
				</svg>
				Back to Check-ins
			</button>
		</div>

		<!-- Swanson Card -->
		<div class="bg-white rounded-2xl shadow-xl overflow-hidden">
			<!-- Header with large Swanson image -->
			<div class="bg-gradient-to-r from-indigo-600 to-indigo-800 px-8 py-6">
				<div class="flex items-center gap-6">
					<img
						src="/swanson.png"
						alt="Swanson"
						class="w-24 h-24 rounded-full object-cover border-4 border-white shadow-lg"
					/>
					<div>
						<h1 class="text-2xl font-bold text-white">Swanson</h1>
						<p class="text-indigo-200">Your no-nonsense recommendation assistant</p>
					</div>
				</div>
			</div>

			<!-- Body -->
			<div class="p-8">
				{#if error && !hasDateFilter}
					<!-- All-time error -->
					<div class="text-center py-8">
						<div class="mb-6">
							<img
								src="/swanson.png"
								alt="Swanson"
								class="w-20 h-20 rounded-full mx-auto opacity-50"
							/>
						</div>
						<p class="text-lg text-gray-700 font-medium mb-4">"{error}"</p>
						<p class="text-gray-500 mb-6">Select a date range on the check-ins page first.</p>
						<button
							on:click={goBack}
							class="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
						>
							Go Back
						</button>
					</div>
				{:else if loading}
					<!-- Loading state with rotating quotes -->
					<div class="text-center py-8">
						<div class="mb-6">
							<img
								src="/swanson.png"
								alt="Swanson thinking"
								class="w-20 h-20 rounded-full mx-auto animate-pulse"
							/>
						</div>
						<div class="mb-4">
							<svg
								class="animate-spin h-8 w-8 text-indigo-600 mx-auto"
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
						<p class="text-lg text-gray-700 italic max-w-md mx-auto">
							"{currentQuote}"
						</p>
					</div>
				{:else if response}
					<!-- Response -->
					<div class="space-y-6">
						<div class="bg-gray-50 rounded-lg p-6">
							<p class="text-gray-800 whitespace-pre-wrap">{response}</p>
						</div>

						<div class="border-t pt-6">
							<p class="text-sm text-gray-500 mb-4">Ask another question:</p>
							<div class="flex gap-3">
								<input
									type="text"
									bind:value={userPrompt}
									on:keydown={handleKeydown}
									placeholder="What else are you in the mood for?"
									class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
								/>
								<button
									on:click={handleSubmit}
									disabled={!userPrompt.trim()}
									class="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
								>
									Ask
								</button>
							</div>
						</div>
					</div>
				{:else}
					<!-- Initial state -->
					<div class="space-y-6">
						{#if error}
							<div class="p-4 bg-red-50 border-l-4 border-red-400 text-red-700 rounded">
								{error}
							</div>
						{/if}

						<div class="text-center mb-6">
							<p class="text-gray-600">
								Based on your <strong>{checkinData.length}</strong> filtered check-ins,
								what are you in the mood for?
							</p>
						</div>

						<textarea
							bind:value={userPrompt}
							on:keydown={handleKeydown}
							placeholder="I'm looking for something like Breaking Bad but funnier..."
							rows="4"
							class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
						/>

						<button
							on:click={handleSubmit}
							disabled={!userPrompt.trim()}
							class="w-full px-6 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
						>
							Ask Swanson
						</button>
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>
