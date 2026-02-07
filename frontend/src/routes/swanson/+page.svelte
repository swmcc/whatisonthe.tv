<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { api } from '$lib/api';

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

	interface Message {
		role: 'user' | 'swanson';
		content: string;
	}

	let messages: Message[] = [];
	let userInput = '';
	let loading = false;
	let currentQuote = '';
	let quoteInterval: ReturnType<typeof setInterval>;
	let checkins: any[] = [];
	let filterInfo: { startDate: string; endDate: string } | null = null;
	let testMode = true; // Set to false for real API calls

	onMount(() => {
		if (browser) {
			const storedCheckins = sessionStorage.getItem('swanson_checkins');
			const storedFilter = sessionStorage.getItem('swanson_filter');
			const storedMessages = sessionStorage.getItem('swanson_messages');

			if (storedCheckins) {
				checkins = JSON.parse(storedCheckins);
			}
			if (storedFilter) {
				filterInfo = JSON.parse(storedFilter);
			}
			if (storedMessages) {
				messages = JSON.parse(storedMessages);
			}

			if (checkins.length === 0) {
				goto('/checkins');
				return;
			}
		}

		currentQuote = getRandomQuote();

		return () => {
			if (quoteInterval) clearInterval(quoteInterval);
		};
	});

	$: if (browser && messages.length > 0) {
		sessionStorage.setItem('swanson_messages', JSON.stringify(messages));
	}

	function getRandomQuote(): string {
		return SWANSON_QUOTES[Math.floor(Math.random() * SWANSON_QUOTES.length)];
	}

	function startQuoteRotation() {
		currentQuote = getRandomQuote();
		quoteInterval = setInterval(() => {
			currentQuote = getRandomQuote();
		}, 3300);
	}

	function stopQuoteRotation() {
		if (quoteInterval) clearInterval(quoteInterval);
	}

	async function sendMessage() {
		if (!userInput.trim() || loading) return;

		const userMessage = userInput.trim();
		userInput = '';

		messages = [...messages, { role: 'user', content: userMessage }];

		loading = true;
		startQuoteRotation();

		try {
			let response: string;

			if (testMode) {
				await new Promise(resolve => setTimeout(resolve, 10000));
				response = `Based on your viewing history, I'd recommend checking out some quality television. You seem to appreciate shows with strong characters and good storytelling. Here are my thoughts on "${userMessage}":\n\n1. Consider rewatching something you loved\n2. Try something completely different\n3. When in doubt, watch Parks and Recreation`;
			} else {
				const searchResults = checkins.map(checkin => ({
					id: checkin.content?.tvdb_id || checkin.content?.id,
					name: checkin.content?.name || 'Unknown',
					type: checkin.content?.content_type || 'unknown',
					year: checkin.content?.year,
					genres: []
				}));

				const result = await api.swanson.recommend({
					prompt: userMessage,
					search_results: searchResults
				});
				response = result.recommendation;
			}

			messages = [...messages, { role: 'swanson', content: response }];
		} catch (err) {
			messages = [...messages, {
				role: 'swanson',
				content: `Something went wrong. ${err instanceof Error ? err.message : 'Try again.'}`
			}];
		} finally {
			loading = false;
			stopQuoteRotation();
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	}

	function goBack() {
		if (browser) {
			sessionStorage.removeItem('swanson_messages');
		}
		goto('/checkins');
	}

	function formatDateRange(): string {
		if (!filterInfo || !filterInfo.startDate) return '';
		const start = new Date(filterInfo.startDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
		const end = new Date(filterInfo.endDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
		return `${start} - ${end}`;
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

<div class="min-h-screen bg-gradient-to-b from-indigo-50 to-white">
	<!-- Header -->
	<div class="bg-white border-b border-gray-200 sticky top-0 z-10">
		<div class="max-w-3xl mx-auto px-4 py-3">
			<div class="flex items-center justify-between">
				<button
					on:click={goBack}
					class="text-gray-600 hover:text-gray-900 flex items-center gap-2 text-sm"
				>
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
					</svg>
					Back to Check-ins
				</button>
				<div class="flex items-center gap-2 text-sm text-gray-500">
					<span class="bg-indigo-100 text-indigo-700 px-2 py-1 rounded-full text-xs font-medium">
						{checkins.length} check-ins
					</span>
					{#if filterInfo && filterInfo.startDate}
						<span class="text-gray-400">|</span>
						<span>{formatDateRange()}</span>
					{/if}
				</div>
			</div>
		</div>
	</div>

	<!-- Chat Area -->
	<div class="max-w-3xl mx-auto px-4 py-6">
		<div class="space-y-6 mb-32">
			{#if messages.length === 0}
				<div class="text-center py-12">
					<img
						src="/swanson.png"
						alt="Swanson"
						class="w-24 h-24 rounded-full mx-auto mb-4 border-4 border-indigo-200"
					/>
					<h1 class="text-2xl font-bold text-gray-900 mb-2">Ask Swanson</h1>
					<p class="text-gray-600 max-w-md mx-auto">
						Based on your {checkins.length} check-ins, I'll give you straight-forward recommendations. No nonsense.
					</p>
				</div>
			{/if}

			{#each messages as message}
				<div class="flex gap-4 {message.role === 'user' ? 'flex-row-reverse' : ''}">
					<div class="flex-shrink-0">
						{#if message.role === 'swanson'}
							<img
								src="/swanson.png"
								alt="Swanson"
								class="w-10 h-10 rounded-full object-cover border-2 border-indigo-200"
							/>
						{:else}
							<div class="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center">
								<svg class="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
								</svg>
							</div>
						{/if}
					</div>

					<div class="flex-1 max-w-xl {message.role === 'user' ? 'text-right' : ''}">
						<div
							class="inline-block px-4 py-3 rounded-2xl {message.role === 'user'
								? 'bg-indigo-600 text-white rounded-br-md'
								: 'bg-white shadow-sm border border-gray-100 rounded-bl-md'}"
						>
							<p class="whitespace-pre-wrap">{message.content}</p>
						</div>
					</div>
				</div>
			{/each}

			{#if loading}
				<div class="flex gap-4">
					<div class="flex-shrink-0">
						<div class="swanson-spin">
							<img
								src="/swanson.png"
								alt="Swanson thinking"
								class="w-10 h-10 rounded-full object-cover border-2 border-indigo-200"
							/>
						</div>
					</div>
					<div class="flex-1">
						<div class="inline-block px-4 py-3 bg-white shadow-sm border border-gray-100 rounded-2xl rounded-bl-md max-w-md">
							<p class="text-gray-600 italic">"{currentQuote}"</p>
							<p class="text-xs text-gray-400 mt-2">- Ron Swanson</p>
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>

	<!-- Input Bar -->
	<div class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4">
		<div class="max-w-3xl mx-auto">
			<div class="flex gap-3 items-end">
				<div class="flex-shrink-0 pb-2">
					<img
						src="/swanson.png"
						alt="Swanson"
						class="w-10 h-10 rounded-full object-cover border-2 border-indigo-300"
						class:swanson-spin={loading}
					/>
				</div>

				<div class="flex-1 relative">
					<textarea
						bind:value={userInput}
						on:keydown={handleKeydown}
						placeholder="Ask me anything about what to watch..."
						rows="1"
						disabled={loading}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none disabled:bg-gray-50 disabled:text-gray-500"
					/>
				</div>

				<button
					on:click={sendMessage}
					disabled={!userInput.trim() || loading}
					class="flex-shrink-0 p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
				>
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
					</svg>
				</button>
			</div>

			{#if testMode}
				<p class="text-xs text-center text-amber-600 mt-2">
					Test mode - 10 second simulated delay
				</p>
			{/if}
		</div>
	</div>
</div>
