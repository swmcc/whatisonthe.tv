<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { api } from '$lib/api';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';

	let searchQuery = '';
	let searchResults: any[] = [];
	let sortedResults: any[] = [];
	let searching = false;
	let loadingMore = false;
	let error = '';
	let hasMore = false;
	let currentOffset = 0;
	const PAGE_SIZE = 20;
	let sortBy: 'relevance' | 'year-desc' | 'year-asc' | 'name-asc' | 'name-desc' = 'relevance';

	const PLACEHOLDER_IMAGE = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="300" height="450"%3E%3Crect fill="%23e5e7eb" width="300" height="450"/%3E%3Ctext fill="%236b7280" font-family="Arial" font-size="20" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3ENo Image%3C/text%3E%3C/svg%3E';

	let scrollTrigger: HTMLDivElement;
	let observer: IntersectionObserver;

	onMount(() => {
		// Restore search from URL parameter
		const urlQuery = $page.url.searchParams.get('q');
		if (urlQuery) {
			searchQuery = urlQuery;
			performSearch();
		}

		// Set up IntersectionObserver for infinite scroll
		observer = new IntersectionObserver(
			(entries) => {
				const entry = entries[0];
				if (entry.isIntersecting && hasMore && !loadingMore && !searching) {
					loadMoreResults();
				}
			},
			{ rootMargin: '100px' }
		);

		return () => {
			if (observer) observer.disconnect();
		};
	});

	$: if (scrollTrigger && observer) {
		observer.observe(scrollTrigger);
	}

	async function performSearch() {
		if (!searchQuery.trim()) return;

		searching = true;
		error = '';
		searchResults = [];
		currentOffset = 0;
		hasMore = false;

		try {
			const response = await api.search.query(searchQuery, PAGE_SIZE, 0);
			searchResults = response.results || [];
			hasMore = response.has_more || false;
			currentOffset = PAGE_SIZE;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Search failed';
		} finally {
			searching = false;
		}
	}

	async function handleSearch(event: Event) {
		event.preventDefault();
		if (!searchQuery.trim()) return;

		// Update URL with search query
		goto(`/?q=${encodeURIComponent(searchQuery)}`, { replaceState: false });

		await performSearch();
	}

	async function loadMoreResults() {
		if (!hasMore || loadingMore || searching) return;

		loadingMore = true;
		try {
			const response = await api.search.query(searchQuery, PAGE_SIZE, currentOffset);
			searchResults = [...searchResults, ...(response.results || [])];
			hasMore = response.has_more || false;
			currentOffset += PAGE_SIZE;
		} catch (err) {
			console.error('Failed to load more results:', err);
		} finally {
			loadingMore = false;
		}
	}

	function getImageUrl(result: any): string {
		return result.image_url || result.poster || '/placeholder.png';
	}

	function getResultUrl(result: any): string {
		const type = result.type?.toLowerCase();
		if (type === 'person') {
			return `/person/${result.id}`;
		} else if (type === 'movie') {
			return `/show/${result.id}?type=movie`;
		} else {
			return `/show/${result.id}`; // Default to show for series
		}
	}

	function sortResults(results: any[]): any[] {
		if (sortBy === 'relevance') {
			return results; // Keep original order (API relevance)
		}

		return [...results].sort((a, b) => {
			switch (sortBy) {
				case 'year-desc':
					return (parseInt(b.year) || 0) - (parseInt(a.year) || 0);
				case 'year-asc':
					return (parseInt(a.year) || 0) - (parseInt(b.year) || 0);
				case 'name-asc':
					return (a.name || '').localeCompare(b.name || '');
				case 'name-desc':
					return (b.name || '').localeCompare(a.name || '');
				default:
					return 0;
			}
		});
	}

	// Reactive statement to re-sort when sortBy or searchResults changes
	$: {
		// Force re-evaluation when sortBy changes
		sortBy;
		sortedResults = sortResults(searchResults);
	}
</script>

<svelte:head>
	<title>What Is On The TV</title>
</svelte:head>

<div class="min-h-[calc(100vh-4rem)] px-4 py-8">
	<div class="w-full max-w-6xl mx-auto">
		<div class="text-center mb-8">
			<div class="flex justify-center mb-4">
				<svg width="120" height="120" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
					<!-- Antenna -->
					<line x1="35" y1="15" x2="25" y2="5" stroke="#8B4513" stroke-width="2" stroke-linecap="round"/>
					<line x1="65" y1="15" x2="75" y2="5" stroke="#8B4513" stroke-width="2" stroke-linecap="round"/>
					<circle cx="25" cy="5" r="2" fill="#8B4513"/>
					<circle cx="75" cy="5" r="2" fill="#8B4513"/>

					<!-- TV Body -->
					<rect x="15" y="20" width="70" height="60" rx="8" fill="#8B4513"/>
					<rect x="18" y="23" width="64" height="54" rx="6" fill="#A0522D"/>

					<!-- Screen -->
					<rect x="23" y="28" width="54" height="38" rx="3" fill="#2D4F67"/>
					<rect x="25" y="30" width="50" height="34" rx="2" fill="#4A90B5" opacity="0.6"/>

					<!-- Control Panel -->
					<circle cx="72" cy="72" r="3" fill="#654321"/>
					<circle cx="65" cy="72" r="2.5" fill="#654321"/>
					<circle cx="58" cy="72" r="2" fill="#654321"/>

					<!-- Speaker grille -->
					<line x1="28" y1="72" x2="48" y2="72" stroke="#654321" stroke-width="1"/>
					<line x1="28" y1="75" x2="48" y2="75" stroke="#654321" stroke-width="1"/>

					<!-- TV Legs -->
					<rect x="28" y="80" width="8" height="10" rx="2" fill="#8B4513"/>
					<rect x="64" y="80" width="8" height="10" rx="2" fill="#8B4513"/>
				</svg>
			</div>
			<p class="text-gray-600">Search for TV shows and movies</p>
		</div>

		<form on:submit={handleSearch} class="w-full max-w-2xl mx-auto mb-8">
			<div class="relative">
				<div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
					<svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
				</div>
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Search for a TV show or movie..."
					class="w-full pl-12 pr-4 py-4 text-lg rounded-full border border-gray-300 shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
				/>
			</div>
			<div class="mt-6 flex gap-3 justify-center">
				<button
					type="submit"
					disabled={searching}
					class="px-6 py-3 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-300 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{searching ? 'Searching...' : 'Search'}
				</button>
			</div>
		</form>

		{#if error}
			<div class="max-w-2xl mx-auto mb-8 bg-red-50 border-l-4 border-red-500 p-4 rounded">
				<p class="text-sm text-red-700">{error}</p>
			</div>
		{/if}

		{#if searchResults.length > 0}
			<div class="mt-8">
				<div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
					<h2 class="text-2xl font-bold text-gray-900">
						Results ({searchResults.length}{hasMore ? '+' : ''})
					</h2>
					<div class="flex items-center gap-2">
						<label for="sort" class="text-sm font-medium text-gray-700">Sort by:</label>
						<select
							id="sort"
							bind:value={sortBy}
							class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
						>
							<option value="relevance">Relevance</option>
							<option value="year-desc">Year (Newest)</option>
							<option value="year-asc">Year (Oldest)</option>
							<option value="name-asc">Name (A-Z)</option>
							<option value="name-desc">Name (Z-A)</option>
						</select>
					</div>
				</div>
				<div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3 sm:gap-4 md:gap-6">
					{#each sortedResults as result}
						<a
							href={getResultUrl(result)}
							class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer block"
						>
							<div class="aspect-[2/3] bg-gray-200 rounded-t-lg overflow-hidden">
								{#if result.image_url || result.poster}
									<img
										src={getImageUrl(result)}
										alt={result.name}
										class="w-full h-full object-cover"
										on:error={(e) => {
											e.currentTarget.src = PLACEHOLDER_IMAGE;
										}}
									/>
								{:else}
									<div class="w-full h-full flex items-center justify-center text-gray-400">
										<svg class="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
										</svg>
									</div>
								{/if}
							</div>
							<div class="p-3">
								<h3 class="font-semibold text-gray-900 text-sm truncate" title={result.name}>
									{result.name || 'Untitled'}
								</h3>
								<div class="flex items-center justify-between mt-1">
									<span class="text-xs text-gray-500">{result.year || 'N/A'}</span>
									{#if result.type}
										<span class="text-xs px-2 py-1 rounded-full bg-indigo-100 text-indigo-700 capitalize">
											{result.type}
										</span>
									{/if}
								</div>
							</div>
						</a>
					{/each}
				</div>

				<!-- Infinite scroll trigger -->
				{#if hasMore}
					<div bind:this={scrollTrigger} class="mt-8 flex justify-center">
						{#if loadingMore}
							<div class="flex items-center gap-2 text-gray-600">
								<svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
								</svg>
								<span>Loading more results...</span>
							</div>
						{:else}
							<div class="text-gray-400 text-sm">Scroll to load more</div>
						{/if}
					</div>
				{:else if searchResults.length > 0}
					<div class="mt-8 text-center text-gray-500 text-sm">
						No more results
					</div>
				{/if}
			</div>
		{:else if !searching && searchQuery}
			<div class="text-center text-gray-500 mt-8">
				No results found for "{searchQuery}"
			</div>
		{/if}
	</div>
</div>
