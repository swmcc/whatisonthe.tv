<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { api } from '$lib/api';

	const dispatch = createEventDispatcher();

	export let checkins: any[] = [];
	export let filterInfo: { startDate: string; endDate: string } | null = null;
	export let testMode = false;

	// 50 Ron Swanson quotes
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
		"Fishing relaxes me. It's like yoga, except I still get to kill something.",
		"I like saying 'No.' It lowers their enthusiasm.",
		"Capitalism: God's way of determining who is smart and who is poor.",
		"I'm not interested in caring about people.",
		"There are only three ways to motivate people: money, fear, and hunger.",
		"Keep your tears in your eyes where they belong.",
		"Normally, if given a choice between doing something and nothing, I'd choose to do nothing. But I will do something if it helps someone else do nothing.",
		"I have cried twice in my life. Once when I was seven and hit by a school bus. And then again when I heard that Li'l Sebastian had passed.",
		"People who buy things are suckers.",
		"Honor. If you don't know what it is, I'm not going to explain it.",
		"Friends: one to three is sufficient.",
		"When I eat, it is the food that is scared.",
		"Breakfast food can serve many purposes.",
		"I don't want to paint with a broad brush here, but every single contractor in the world is a criminal.",
		"Great job, everyone. The reception will be held in each of our individual houses, alone.",
		"There has never been a sadness that can't be cured by breakfast food.",
		"I am not a sore loser. It's just that I prefer to win and when I don't, I get furious.",
		"Turkey can never beat cow.",
		"Please and thank you. That's how it's done.",
		"I call this turf 'n' turf. It's a 16-oz T-bone and a 24-oz porterhouse.",
		"On my deathbed, my final wish is to have my ex-wives rush to my side so I can use my dying breath to tell them both to go to hell one last time.",
		"Under my tutelage, you will grow from boys to men. From men into gladiators. And from gladiators into Swansons.",
		"I suffer from a condition called 'caring too little.'",
		"I don't drink alcohol from feminine containers. Glass? Plastic? Lady glass.",
		"You had me at 'Meat Tornado.'",
		"Put some alcohol in your mouth to block the words from coming out.",
		"I'm a man of simple pleasures. Give me a well-cooked steak, a glass of whiskey, and a room full of people I can ignore.",
		"The only things I care about are golf, meat, and my relationships with my female companions.",
		"I've said too much. Any more details and I might have feelings.",
		"If there were more food and fewer people, this would be a perfect party.",
		"Everything hurts. Running is impossible.",
		"No home is complete without a proper toolbox. Fill yours with items you'll actually use.",
		"I like Tom. He doesn't do a lot of work around here. He shows zero initiative. He's not a team player. He's never wanted to go that extra mile. Tom is exactly what I'm looking for in a government employee.",
		"I know what I'm about, son.",
		"Cultivate relationships. But not too many.",
		"Live your life how you want, but don't confuse drama with happiness."
	];

	let userPrompt = '';
	let loading = false;
	let error = '';
	let currentQuote = '';
	let quoteInterval: ReturnType<typeof setInterval>;

	// Initialize with a random quote
	currentQuote = getRandomQuote();

	function getRandomQuote(): string {
		return SWANSON_QUOTES[Math.floor(Math.random() * SWANSON_QUOTES.length)];
	}

	function startLoadingAnimation() {
		currentQuote = getRandomQuote();
		// Rotate quotes every 3.3 seconds (3 quotes in 10 seconds)
		quoteInterval = setInterval(() => {
			currentQuote = getRandomQuote();
		}, 3300);
	}

	function stopLoadingAnimation() {
		if (quoteInterval) clearInterval(quoteInterval);
	}

	async function handleSubmit() {
		if (!userPrompt.trim()) return;

		loading = true;
		error = '';
		startLoadingAnimation();

		try {
			let aiResponse: string;

			if (testMode) {
				// Test mode - wait 10 seconds to see the loading state
				await new Promise(resolve => setTimeout(resolve, 10000));
				aiResponse = "Based on your viewing history, I'd recommend checking out some quality television. You seem to appreciate shows with strong characters and good storytelling.";
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
				aiResponse = result.recommendation;
			}

			// Store context and navigate to Swanson page
			if (browser) {
				sessionStorage.setItem('swanson_checkins', JSON.stringify(checkins));
				sessionStorage.setItem('swanson_filter', JSON.stringify(filterInfo || {}));
				sessionStorage.setItem('swanson_messages', JSON.stringify([
					{ role: 'user', content: userPrompt },
					{ role: 'swanson', content: aiResponse }
				]));
			}

			stopLoadingAnimation();
			// Navigate to Swanson chat page
			goto('/swanson');

		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to get recommendation';
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
</script>

<style>
	@keyframes spin-slow {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	.swanson-spin {
		animation: spin-slow 2s linear infinite;
	}
</style>

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
					<div class:swanson-spin={loading}>
						<img
							src="/swanson.png"
							alt="Swanson"
							class="w-16 h-16 rounded-full object-cover border-4 border-white shadow-lg"
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
				<!-- Loading State - Spinning Swanson head with quote -->
				<div class="text-center py-8">
					<div class="mb-6">
						<div class="swanson-spin inline-block">
							<img
								src="/swanson.png"
								alt="Swanson thinking"
								class="w-24 h-24 rounded-full object-cover border-4 border-indigo-200 shadow-lg"
							/>
						</div>
					</div>
					<p class="text-lg text-gray-700 italic max-w-sm mx-auto leading-relaxed">
						"{currentQuote}"
					</p>
					<p class="text-xs text-gray-400 mt-4">- Ron Swanson</p>
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
							Test mode - 10 second simulated delay
						</p>
					{/if}
				</div>
			{/if}
		</div>
	</div>
</div>
