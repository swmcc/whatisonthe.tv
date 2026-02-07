<script lang="ts">
	import { onMount, afterUpdate } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { api } from '$lib/api';
	import { auth } from '$lib/stores/auth';
	import { swansonLoading, swansonStreamingText, swansonMessages, resetSwansonStores, parseTitles, collectFeedback, collectPreviousRecommendations, type SearchResult, type Rating } from '$lib/stores/swanson';

	// Simple streaming-safe markdown renderer
	function renderMarkdown(text: string): string {
		let html = text
			// Escape HTML first
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			// Bold: **text** - only match complete pairs
			.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
			// Italic: *text* - only match complete pairs (but not inside bold)
			.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>')
			// Bullet points: lines starting with -
			.replace(/^- (.+)$/gm, '<li>$1</li>')
			// Wrap consecutive <li> in <ul>
			.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
			// Double newlines = paragraph break
			.replace(/\n\n/g, '</p><p>')
			// Single newlines = line break
			.replace(/\n/g, '<br>');

		// Wrap in paragraph tags
		html = '<p>' + html + '</p>';
		// Clean up empty paragraphs
		html = html.replace(/<p><\/p>/g, '');

		return html;
	}

	let chatBottom: HTMLDivElement;

	function scrollToBottom() {
		if (chatBottom) {
			chatBottom.scrollIntoView({ behavior: 'smooth' });
		}
	}

	afterUpdate(() => {
		if ($swansonMessages.length > 0 || $swansonLoading) {
			scrollToBottom();
		}
	});

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

	let userInput = '';
	let currentQuote = "Never half-ass two things. Whole-ass one thing.";
	let quoteInterval: ReturnType<typeof setInterval>;

	let checkins: any[] = [];
	let searchResults: any[] = [];
	let filterInfo: { startDate: string; endDate: string } | null = null;

	onMount(async () => {
		// Reset global stores on mount
		resetSwansonStores();

		if (browser) {
			const storedCheckins = sessionStorage.getItem('swanson_checkins');
			const storedFilter = sessionStorage.getItem('swanson_filter');
			const storedMessages = sessionStorage.getItem('swanson_messages');
			const storedSearchResults = sessionStorage.getItem('swanson_search_results');
			const pendingPrompt = sessionStorage.getItem('swanson_pending_prompt');

			if (storedCheckins) checkins = JSON.parse(storedCheckins);
			if (storedFilter) filterInfo = JSON.parse(storedFilter);
			if (storedMessages) swansonMessages.set(JSON.parse(storedMessages));
			if (storedSearchResults) searchResults = JSON.parse(storedSearchResults);

			if (checkins.length === 0) {
				goto('/checkins');
				return;
			}

			// If there's a pending prompt, defer to next frame to ensure component is ready
			if (pendingPrompt) {
				sessionStorage.removeItem('swanson_pending_prompt');
				setTimeout(() => {
					streamResponse(pendingPrompt);
				}, 0);
			}
		}

		currentQuote = getRandomQuote();

		return () => {
			if (quoteInterval) clearInterval(quoteInterval);
		};
	});

	$: if (browser && $swansonMessages.length > 0) {
		sessionStorage.setItem('swanson_messages', JSON.stringify($swansonMessages));
	}

	function getRandomQuote(): string {
		return SWANSON_QUOTES[Math.floor(Math.random() * SWANSON_QUOTES.length)];
	}

	function startQuoteRotation() {
		if (quoteInterval) clearInterval(quoteInterval);
		currentQuote = getRandomQuote();
		quoteInterval = setInterval(() => {
			currentQuote = getRandomQuote();
		}, 3300);
	}

	function stopQuoteRotation() {
		if (quoteInterval) clearInterval(quoteInterval);
	}

	async function searchForTitles(titles: string[]): Promise<SearchResult[]> {
		const results: SearchResult[] = [];
		const seen = new Set<number>();

		for (const title of titles.slice(0, 5)) {
			try {
				const searchResponse = await api.search.query(title, 1);
				if (searchResponse.results && searchResponse.results.length > 0) {
					const item = searchResponse.results[0];
					if (item.id && !seen.has(item.id)) {
						seen.add(item.id);
						results.push({
							id: item.id,
							name: item.name,
							type: item.type,
							year: item.year ? parseInt(item.year) : undefined,
							image: item.image_url
						});
					}
				}
			} catch (e) {
				console.error('Failed to search for:', title, e);
			}
		}
		return results;
	}

	function rateRecommendation(messageIndex: number, recIndex: number, rating: Rating) {
		swansonMessages.update(msgs => {
			const newMsgs = [...msgs];
			const msg = newMsgs[messageIndex];
			if (msg.recommendations && msg.recommendations[recIndex]) {
				const rec = msg.recommendations[recIndex];
				// Toggle off if clicking the same rating
				rec.rating = rec.rating === rating ? undefined : rating;
			}
			return newMsgs;
		});
	}

	async function streamResponse(prompt: string) {
		swansonMessages.update(msgs => [...msgs, { role: 'user', content: prompt }]);
		swansonLoading.set(true);
		swansonStreamingText.set('');
		startQuoteRotation();

		// Collect feedback and previous recommendations
		const feedback = collectFeedback();
		const previousRecs = collectPreviousRecommendations();

		try {
			let accumulated = '';
			for await (const chunk of api.swanson.stream({
				prompt,
				search_results: searchResults,
				feedback: feedback.length > 0 ? feedback : undefined,
				previous_recommendations: previousRecs.length > 0 ? previousRecs : undefined
			})) {
				accumulated += chunk;
				swansonStreamingText.set(accumulated);
			}

			// Parse titles and search for recommendations
			const { cleanContent, titles } = parseTitles(accumulated);
			let recommendations: SearchResult[] = [];
			if (titles.length > 0) {
				recommendations = await searchForTitles(titles);
			}

			swansonMessages.update(msgs => [...msgs, {
				role: 'swanson',
				content: cleanContent,
				recommendations
			}]);
			swansonStreamingText.set('');
		} catch (err) {
			swansonMessages.update(msgs => [...msgs, {
				role: 'swanson',
				content: `Something went wrong. ${err instanceof Error ? err.message : 'Try again.'}`
			}]);
		} finally {
			swansonLoading.set(false);
			stopQuoteRotation();
		}
	}

	async function sendMessage() {
		if (!userInput.trim() || $swansonLoading) return;

		const prompt = userInput.trim();
		userInput = '';

		await streamResponse(prompt);
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
			sessionStorage.removeItem('swanson_pending_prompt');
		}
		swansonMessages.set([]);
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

	/* Markdown prose styles */
	.prose :global(p) {
		margin-bottom: 0.75rem;
	}
	.prose :global(p:last-child) {
		margin-bottom: 0;
	}
	.prose :global(ul) {
		list-style-type: disc !important;
		margin: 0.75rem 0 !important;
		padding-left: 1.5rem !important;
	}
	.prose :global(ol) {
		list-style-type: decimal !important;
		margin: 0.75rem 0 !important;
		padding-left: 1.5rem !important;
	}
	.prose :global(li) {
		margin-bottom: 0.375rem !important;
		display: list-item !important;
	}
	.prose :global(li p) {
		margin-bottom: 0;
	}
	.prose :global(strong) {
		font-weight: 600;
	}
	.prose :global(em) {
		font-style: italic;
	}
	.prose :global(h1), .prose :global(h2), .prose :global(h3) {
		font-weight: 600;
		margin-top: 1rem;
		margin-bottom: 0.5rem;
	}
	.prose :global(br) {
		display: block;
		content: "";
		margin-top: 0.5rem;
	}
	.prose :global(code) {
		background-color: #f3f4f6;
		padding: 0.125rem 0.25rem;
		border-radius: 0.25rem;
		font-size: 0.875em;
	}
</style>

<!-- Sub-header with context -->
<div class="bg-gradient-to-b from-indigo-50 to-white border-b border-gray-200">
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
			{#if $swansonMessages.length === 0 && !$swansonLoading}
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

			{#each $swansonMessages as message}
				<div class="flex gap-4 {message.role === 'user' ? 'flex-row-reverse' : ''}">
					<div class="flex-shrink-0">
						{#if message.role === 'swanson'}
							<img
								src="/swanson.png"
								alt="Swanson"
								class="w-10 h-10 rounded-full object-cover border-2 border-indigo-200"
							/>
						{:else}
							<div class="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-medium">
								{$auth.user?.first_name?.[0] || ''}{$auth.user?.last_name?.[0] || ''}
							</div>
						{/if}
					</div>

					<div class="flex-1 max-w-xl {message.role === 'user' ? 'text-right' : ''}">
						<div
							class="inline-block px-4 py-3 rounded-2xl {message.role === 'user'
								? 'bg-indigo-600 text-white rounded-br-md'
								: 'bg-white shadow-sm border border-gray-100 rounded-bl-md'}"
						>
							{#if message.role === 'swanson'}
								<div class="prose prose-sm max-w-none">{@html renderMarkdown(message.content)}</div>
							{:else}
								<p class="whitespace-pre-wrap">{message.content}</p>
							{/if}
						</div>

						{#if message.role === 'swanson' && message.recommendations && message.recommendations.length > 0}
							{@const messageIndex = $swansonMessages.indexOf(message)}
							<div class="mt-4 flex flex-wrap gap-4">
								{#each message.recommendations as rec, recIndex}
									<div class="group flex items-center gap-4 px-4 py-3 rounded-2xl bg-gray-50 border border-gray-200 shadow-sm">
										<a
											href="/show/{rec.id}{rec.type === 'movie' ? '?type=movie' : ''}"
											class="flex items-center gap-4 hover:opacity-80 transition-opacity"
										>
											{#if rec.image}
												<img
													src={rec.image}
													alt={rec.name}
													class="w-14 h-20 rounded-lg object-cover shadow-sm"
												/>
											{:else}
												<div class="w-14 h-20 rounded-lg bg-gradient-to-br from-indigo-100 to-indigo-200 flex items-center justify-center shadow-sm">
													<svg class="w-6 h-6 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
													</svg>
												</div>
											{/if}
											<div class="min-w-0">
												<p class="text-base font-medium text-gray-900 truncate max-w-[140px]">{rec.name}</p>
												<p class="text-sm text-gray-500">{rec.type === 'movie' ? 'Movie' : 'Series'}{rec.year ? ` · ${rec.year}` : ''}</p>
											</div>
										</a>
										<div class="flex gap-1 ml-auto pl-2 border-l border-gray-200">
											<button
												on:click={() => rateRecommendation(messageIndex, recIndex, 'dislike')}
												class="p-1.5 rounded-full transition-colors {rec.rating === 'dislike' ? 'text-red-500 bg-red-50' : 'text-gray-300 hover:text-gray-400 hover:bg-gray-100'}"
												title="Not interested"
											>
												<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M10 15v4a3 3 0 003 3l4-9V2H5.72a2 2 0 00-2 1.7l-1.38 9a2 2 0 002 2.3zm7-13h2.67A2.31 2.31 0 0122 4v7a2.31 2.31 0 01-2.33 2H17" />
												</svg>
											</button>
											<button
												on:click={() => rateRecommendation(messageIndex, recIndex, 'like')}
												class="p-1.5 rounded-full transition-colors {rec.rating === 'like' ? 'text-indigo-500 bg-indigo-50' : 'text-gray-300 hover:text-gray-400 hover:bg-gray-100'}"
												title="Interested"
											>
												<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3zM7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3" />
												</svg>
											</button>
											<button
												on:click={() => rateRecommendation(messageIndex, recIndex, 'love')}
												class="p-1.5 rounded-full transition-colors {rec.rating === 'love' ? 'text-yellow-500 bg-yellow-50' : 'text-gray-300 hover:text-gray-400 hover:bg-gray-100'}"
												title="Very interested"
											>
												<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
													<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
												</svg>
											</button>
										</div>
									</div>
								{/each}
							</div>
						{/if}
					</div>
				</div>
			{/each}

			{#if $swansonLoading}
				<div class="flex gap-4">
					<div class="flex-shrink-0">
						<img
							src="/swanson.png"
							alt="Swanson thinking"
							class="w-10 h-10 rounded-full object-cover border-2 border-indigo-200 swanson-spin"
						/>
					</div>
					<div class="flex-1">
						<div class="inline-block px-4 py-3 bg-white shadow-sm border border-gray-100 rounded-2xl rounded-bl-md max-w-xl">
							{#if $swansonStreamingText}
								<div class="prose prose-sm max-w-none">{@html renderMarkdown($swansonStreamingText)}<span class="animate-pulse">▊</span></div>
							{:else}
								<p class="text-gray-600 italic">"{currentQuote}"</p>
								<p class="text-xs text-gray-400 mt-2">- Ron Swanson</p>
							{/if}
						</div>
					</div>
				</div>
			{/if}
			<div bind:this={chatBottom}></div>
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
						class:swanson-spin={$swansonLoading}
					/>
				</div>

				<div class="flex-1 relative">
					<textarea
						bind:value={userInput}
						on:keydown={handleKeydown}
						placeholder="Ask me anything about what to watch..."
						rows="1"
						disabled={$swansonLoading}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none disabled:bg-gray-50 disabled:text-gray-500"
					/>
				</div>

				<button
					on:click={sendMessage}
					disabled={!userInput.trim() || $swansonLoading}
					class="flex-shrink-0 p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
				>
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
					</svg>
				</button>
			</div>
		</div>
	</div>
