<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { goto } from '$app/navigation';

	let loading = true;
	let error = '';
	let data: any = null;
	let activeTab = 'series';
	let sortBy: 'year-desc' | 'year-asc' | 'name-asc' | 'name-desc' = 'year-desc';

	const id = $page.params.id;

	onMount(async () => {
		await loadPersonDetails();
	});

	async function loadPersonDetails() {
		loading = true;
		error = '';

		try {
			const response = await api.search.getPerson(parseInt(id));
			data = response;

			// Determine default tab based on which has more entries
			const seriesCount = data.characters?.filter((c: any) => c.seriesId)?.length || 0;
			const movieCount = data.characters?.filter((c: any) => c.movieId)?.length || 0;
			activeTab = seriesCount >= movieCount ? 'series' : 'movies';
		} catch (personError) {
			error = 'Failed to load person details';
		} finally {
			loading = false;
		}
	}

	const PLACEHOLDER_PERSON = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="500" height="750"%3E%3Crect fill="%23e5e7eb" width="500" height="750"/%3E%3Ctext fill="%236b7280" font-family="Arial" font-size="24" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3ENo Image%3C/text%3E%3C/svg%3E';
	const PLACEHOLDER_POSTER = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="300" height="450"%3E%3Crect fill="%23e5e7eb" width="300" height="450"/%3E%3Ctext fill="%236b7280" font-family="Arial" font-size="20" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3ENo Poster%3C/text%3E%3C/svg%3E';

	function getPersonImage(imageUrl: string | null | undefined): string {
		if (!imageUrl) return PLACEHOLDER_PERSON;
		return imageUrl;
	}

	function getPosterUrl(item: any): string {
		if (item.image) return item.image;
		return PLACEHOLDER_POSTER;
	}

	function getEnglishAliases(aliases: any[] | undefined): string[] {
		if (!aliases) return [];
		return aliases
			.filter((a) => a.language === 'eng')
			.map((a) => a.name)
			.filter((name, index, self) => self.indexOf(name) === index); // Remove duplicates
	}

	function getUniqueCredits(characters: any[]): any[] {
		if (!characters) return [];

		// Group credits by content ID
		const creditMap = new Map();

		for (const credit of characters) {
			const contentId = credit.seriesId || credit.movieId;
			if (!contentId) continue;

			if (!creditMap.has(contentId)) {
				// First credit for this content - store it with role types array
				creditMap.set(contentId, {
					...credit,
					roles: [credit.peopleType],
					characterNames: credit.name ? [credit.name] : []
				});
			} else {
				// Add additional role types and character names
				const existing = creditMap.get(contentId);
				if (credit.peopleType && !existing.roles.includes(credit.peopleType)) {
					existing.roles.push(credit.peopleType);
				}
				if (credit.name && !existing.characterNames.includes(credit.name)) {
					existing.characterNames.push(credit.name);
				}
			}
		}

		return Array.from(creditMap.values());
	}

	function sortCredits(credits: any[]): any[] {
		return [...credits].sort((a, b) => {
			const aContent = a.series || a.movie;
			const bContent = b.series || b.movie;

			switch (sortBy) {
				case 'year-desc':
					return (parseInt(bContent?.year) || 0) - (parseInt(aContent?.year) || 0);
				case 'year-asc':
					return (parseInt(aContent?.year) || 0) - (parseInt(bContent?.year) || 0);
				case 'name-asc':
					return (aContent?.name || '').localeCompare(bContent?.name || '');
				case 'name-desc':
					return (bContent?.name || '').localeCompare(aContent?.name || '');
				default:
					return 0;
			}
		});
	}
</script>

<svelte:head>
	<title>{data?.name || 'Loading...'} - What Is On The TV</title>
</svelte:head>

{#if loading}
	<div class="flex items-center justify-center min-h-[50vh]">
		<div class="text-center">
			<svg class="animate-spin h-12 w-12 text-indigo-600 mx-auto" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
			</svg>
			<p class="mt-4 text-gray-600">Loading...</p>
		</div>
	</div>
{:else if error}
	<div class="max-w-2xl mx-auto mt-8 bg-red-50 border-l-4 border-red-500 p-4 rounded">
		<p class="text-sm text-red-700">{error}</p>
		<button
			on:click={() => window.history.back()}
			class="mt-4 text-indigo-600 hover:text-indigo-800"
		>
			← Back
		</button>
	</div>
{:else if data}
	<div class="max-w-7xl mx-auto px-4 py-8">
		<!-- Back button -->
		<button
			on:click={() => window.history.back()}
			class="mb-6 text-indigo-600 hover:text-indigo-800 flex items-center gap-2"
		>
			<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
			</svg>
			Back
		</button>

		<!-- Header Section -->
		<div class="bg-white rounded-lg shadow-lg overflow-hidden mb-8">
			<div class="md:flex">
				<!-- Person Image -->
				<div class="md:w-1/3 lg:w-1/4">
					<img
						src={getPersonImage(data.image)}
						alt={data.name}
						class="w-full h-auto object-cover"
						on:error={(e) => {
							e.currentTarget.src = PLACEHOLDER_PERSON;
						}}
					/>
				</div>

				<!-- Info -->
				<div class="md:w-2/3 lg:w-3/4 p-6">
					<h1 class="text-4xl font-bold text-gray-900 mb-4">{data.name}</h1>

					<!-- Aliases -->
					{#if data.aliases && getEnglishAliases(data.aliases).length > 0}
						{@const englishAliases = getEnglishAliases(data.aliases)}
						<div class="mb-4">
							<h3 class="text-sm font-semibold text-gray-700 mb-2">Also known as</h3>
							<div class="flex flex-wrap gap-2">
								{#each englishAliases as alias}
									<span class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
										{alias}
									</span>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Biography -->
					{#if data.biography}
						<div class="mb-4">
							<h2 class="text-xl font-bold text-gray-900 mb-2">Biography</h2>
							<p class="text-gray-700 leading-relaxed">{data.biography}</p>
						</div>
					{/if}
				</div>
			</div>
		</div>

		<!-- Filmography -->
		{#if data.characters && data.characters.length > 0}
			{@const uniqueCharacters = getUniqueCredits(data.characters)}
			{@const seriesCredits = uniqueCharacters.filter((c) => c.seriesId && c.series)}
			{@const movieCredits = uniqueCharacters.filter((c) => c.movieId && c.movie)}

			<div class="bg-white rounded-lg shadow-lg p-6">
				<div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
					<h2 class="text-2xl font-bold text-gray-900">Filmography</h2>
					<div class="flex items-center gap-2">
						<label for="sort-filmography" class="text-sm font-medium text-gray-700">Sort by:</label>
						<select
							id="sort-filmography"
							bind:value={sortBy}
							class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
						>
							<option value="year-desc">Year (Newest)</option>
							<option value="year-asc">Year (Oldest)</option>
							<option value="name-asc">Name (A-Z)</option>
							<option value="name-desc">Name (Z-A)</option>
						</select>
					</div>
				</div>

				<!-- Tabs -->
				<div class="border-b border-gray-200 mb-6">
					<nav class="-mb-px flex space-x-8">
						{#if seriesCredits.length > 0}
							<button
								on:click={() => activeTab = 'series'}
								class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
									{activeTab === 'series' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
							>
								Series ({seriesCredits.length})
							</button>
						{/if}
						{#if movieCredits.length > 0}
							<button
								on:click={() => activeTab = 'movies'}
								class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
									{activeTab === 'movies' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
							>
								Movies ({movieCredits.length})
							</button>
						{/if}
					</nav>
				</div>

				<!-- Tab Content -->
				<div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3 sm:gap-4 md:gap-6">
					{#if activeTab === 'series'}
						{#key sortBy}
							{#each sortCredits(seriesCredits) as credit}
							{@const series = credit.series}
							{#if series}
								<a
									href="/show/{credit.seriesId}"
									class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer block"
								>
									<div class="aspect-[2/3] bg-gray-200 rounded-t-lg overflow-hidden">
										<img
											src={getPosterUrl(series)}
											alt={series.name}
											class="w-full h-full object-cover"
											on:error={(e) => {
												e.currentTarget.src = PLACEHOLDER_POSTER;
											}}
										/>
									</div>
									<div class="p-3">
										<h3 class="font-semibold text-gray-900 text-sm truncate" title={series.name}>
											{series.name || 'Untitled'}
										</h3>
										<div class="flex items-center justify-between mt-1">
											<span class="text-xs text-gray-500">{series.year || 'N/A'}</span>
										</div>
										{#if credit.characterNames && credit.characterNames.length > 0}
											<p class="text-xs text-gray-600 mt-1 truncate" title={credit.characterNames.join(', ')}>
												as {credit.characterNames.join(', ')}
											</p>
										{/if}
										{#if credit.roles && credit.roles.length > 0}
											<p class="text-xs text-indigo-600 mt-1 truncate" title={credit.roles.join(', ')}>
												{credit.roles.join(', ')}
											</p>
										{/if}
									</div>
								</a>
							{/if}
							{/each}
						{/key}
					{:else if activeTab === 'movies'}
						{#key sortBy}
							{#each sortCredits(movieCredits) as credit}
							{@const movie = credit.movie}
							{#if movie}
								<a
									href="/show/{credit.movieId}"
									class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer block"
								>
									<div class="aspect-[2/3] bg-gray-200 rounded-t-lg overflow-hidden">
										<img
											src={getPosterUrl(movie)}
											alt={movie.name}
											class="w-full h-full object-cover"
											on:error={(e) => {
												e.currentTarget.src = PLACEHOLDER_POSTER;
											}}
										/>
									</div>
									<div class="p-3">
										<h3 class="font-semibold text-gray-900 text-sm truncate" title={movie.name}>
											{movie.name || 'Untitled'}
										</h3>
										<div class="flex items-center justify-between mt-1">
											<span class="text-xs text-gray-500">{movie.year || 'N/A'}</span>
										</div>
										{#if credit.characterNames && credit.characterNames.length > 0}
											<p class="text-xs text-gray-600 mt-1 truncate" title={credit.characterNames.join(', ')}>
												as {credit.characterNames.join(', ')}
											</p>
										{/if}
										{#if credit.roles && credit.roles.length > 0}
											<p class="text-xs text-indigo-600 mt-1 truncate" title={credit.roles.join(', ')}>
												{credit.roles.join(', ')}
											</p>
										{/if}
									</div>
								</a>
							{/if}
							{/each}
						{/key}
					{/if}
				</div>
			</div>
		{/if}
	</div>
{/if}
