<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { api } from '$lib/api';

	let searchQuery = '';
	let searchResults: any[] = [];
	let searching = false;
	let error = '';

	async function handleSearch(event: Event) {
		event.preventDefault();
		if (!searchQuery.trim()) return;

		searching = true;
		error = '';
		searchResults = [];

		try {
			const response = await api.search.query(searchQuery, 20);
			searchResults = response.results || [];
		} catch (err) {
			error = err instanceof Error ? err.message : 'Search failed';
		} finally {
			searching = false;
		}
	}

	function getImageUrl(result: any): string {
		return result.image_url || result.poster || '/placeholder.png';
	}
</script>

<svelte:head>
	<title>What Is On The TV</title>
</svelte:head>

<div class="min-h-[calc(100vh-4rem)] px-4 py-8">
	<div class="w-full max-w-6xl mx-auto">
		<div class="text-center mb-8">
			<h1 class="text-5xl font-bold text-gray-900 mb-2">
				What Is On The TV
			</h1>
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
				<h2 class="text-2xl font-bold text-gray-900 mb-6">Results ({searchResults.length})</h2>
				<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
					{#each searchResults as result}
						<div class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer">
							<div class="aspect-[2/3] bg-gray-200 rounded-t-lg overflow-hidden">
								{#if result.image_url || result.poster}
									<img
										src={getImageUrl(result)}
										alt={result.name}
										class="w-full h-full object-cover"
										on:error={(e) => {
											e.currentTarget.src = 'https://via.placeholder.com/300x450?text=No+Image';
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
						</div>
					{/each}
				</div>
			</div>
		{:else if !searching && searchQuery}
			<div class="text-center text-gray-500 mt-8">
				No results found for "{searchQuery}"
			</div>
		{/if}
	</div>
</div>
