<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { goto } from '$app/navigation';

	let loading = true;
	let error = '';
	let data: any = null;
	let isSeries = true;
	let activeTab = 'actors';

	const id = $page.params.id;

	onMount(async () => {
		await loadDetails();
	});

	async function loadDetails() {
		loading = true;
		error = '';

		try {
			// Try series first
			const response = await api.search.getSeries(parseInt(id));
			data = response;
			isSeries = true;
		} catch (seriesError) {
			// If series fails, try movie
			try {
				const response = await api.search.getMovie(parseInt(id));
				data = response;
				isSeries = false;
			} catch (movieError) {
				error = 'Failed to load details';
			}
		} finally {
			loading = false;
		}
	}

	function getPosterUrl(imageUrl: string | null | undefined): string {
		if (!imageUrl) return 'https://via.placeholder.com/500x750?text=No+Poster';
		return imageUrl;
	}

	function getCharacterImage(character: any): string {
		if (character.image) return character.image;
		if (character.personImgURL) return character.personImgURL;
		return 'https://via.placeholder.com/150x150?text=No+Image';
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
			on:click={() => goto('/')}
			class="mt-4 text-indigo-600 hover:text-indigo-800"
		>
			← Back to search
		</button>
	</div>
{:else if data}
	<div class="max-w-7xl mx-auto px-4 py-8">
		<!-- Back button -->
		<button
			on:click={() => goto('/')}
			class="mb-6 text-indigo-600 hover:text-indigo-800 flex items-center gap-2"
		>
			<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
			</svg>
			Back to search
		</button>

		<!-- Header Section -->
		<div class="bg-white rounded-lg shadow-lg overflow-hidden mb-8">
			<div class="md:flex">
				<!-- Poster -->
				<div class="md:w-1/3 lg:w-1/4">
					<img
						src={getPosterUrl(data.image)}
						alt={data.name}
						class="w-full h-auto object-cover"
						on:error={(e) => {
							e.currentTarget.src = 'https://via.placeholder.com/500x750?text=No+Poster';
						}}
					/>
				</div>

				<!-- Info -->
				<div class="md:w-2/3 lg:w-3/4 p-6">
					<div class="flex items-start justify-between mb-4">
						<div>
							<h1 class="text-4xl font-bold text-gray-900 mb-2">{data.name}</h1>
							{#if data.aliases && data.aliases.length > 0}
								{@const englishAliases = data.aliases.filter(a => a.language === 'eng')}
								{#if englishAliases.length > 0}
									<div class="text-sm text-gray-600 mb-2">
										<span class="font-semibold">Also known as:</span>
										{englishAliases.slice(0, 3).map((a) => a.name).join(', ')}
									</div>
								{/if}
							{/if}
						</div>
						{#if data.status}
							{@const statusName = typeof data.status === 'string' ? data.status : data.status?.name}
							<span class="px-4 py-2 rounded-full text-sm font-semibold
								{statusName === 'Continuing' || statusName === 'Released' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}">
								{statusName}
							</span>
						{/if}
					</div>

					<!-- Meta Info -->
					<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
						{#if data.year}
							<div>
								<p class="text-sm text-gray-500">Year</p>
								<p class="font-semibold text-gray-900">{data.year}</p>
							</div>
						{/if}
						{#if data.originalCountry}
							<div>
								<p class="text-sm text-gray-500">Country</p>
								<p class="font-semibold text-gray-900">{data.originalCountry}</p>
							</div>
						{/if}
						{#if data.originalLanguage}
							<div>
								<p class="text-sm text-gray-500">Language</p>
								<p class="font-semibold text-gray-900">{data.originalLanguage}</p>
							</div>
						{/if}
						{#if data.averageRuntime || data.runtime}
							<div>
								<p class="text-sm text-gray-500">Runtime</p>
								<p class="font-semibold text-gray-900">{data.averageRuntime || data.runtime} min</p>
							</div>
						{/if}
					</div>

					<!-- Synopsis -->
					{#if data.overview}
						<div class="mb-6">
							<h2 class="text-xl font-bold text-gray-900 mb-2">Synopsis</h2>
							<p class="text-gray-700 leading-relaxed">{data.overview}</p>
						</div>
					{/if}

					<!-- Genres -->
					{#if data.genres && data.genres.length > 0}
						<div class="mb-4">
							<h3 class="text-sm font-semibold text-gray-700 mb-2">Genres</h3>
							<div class="flex flex-wrap gap-2">
								{#each data.genres as genre}
									<span class="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm">
										{genre.name}
									</span>
								{/each}
							</div>
						</div>
					{/if}
				</div>
			</div>
		</div>

		<!-- Cast & Crew -->
		{#if data.characters && data.characters.length > 0}
			{@const sortedCharacters = [...data.characters].sort((a, b) => (a.sort || 999) - (b.sort || 999))}
			{@const actors = sortedCharacters.filter(c => c.peopleType === 'Actor')}
			{@const directors = sortedCharacters.filter(c => c.peopleType === 'Director')}
			{@const writers = sortedCharacters.filter(c => c.peopleType === 'Writer')}
			{@const producers = sortedCharacters.filter(c => c.peopleType === 'Executive Producer' || c.peopleType === 'Producer')}
			{@const otherCrew = sortedCharacters.filter(c => c.peopleType !== 'Actor' && c.peopleType !== 'Director' && c.peopleType !== 'Writer' && c.peopleType !== 'Executive Producer' && c.peopleType !== 'Producer')}

			<div class="bg-white rounded-lg shadow-lg p-6">
				<h2 class="text-2xl font-bold text-gray-900 mb-6">Cast & Crew</h2>

				<!-- Tabs -->
				<div class="border-b border-gray-200 mb-6">
					<nav class="-mb-px flex space-x-8">
						{#if actors.length > 0}
							<button
								on:click={() => activeTab = 'actors'}
								class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
									{activeTab === 'actors' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
							>
								Cast ({actors.length})
							</button>
						{/if}
						{#if directors.length > 0}
							<button
								on:click={() => activeTab = 'directors'}
								class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
									{activeTab === 'directors' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
							>
								Directors ({directors.length})
							</button>
						{/if}
						{#if writers.length > 0}
							<button
								on:click={() => activeTab = 'writers'}
								class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
									{activeTab === 'writers' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
							>
								Writers ({writers.length})
							</button>
						{/if}
						{#if producers.length > 0}
							<button
								on:click={() => activeTab = 'producers'}
								class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
									{activeTab === 'producers' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
							>
								Producers ({producers.length})
							</button>
						{/if}
						{#if otherCrew.length > 0}
							<button
								on:click={() => activeTab = 'other'}
								class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
									{activeTab === 'other' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
							>
								Other ({otherCrew.length})
							</button>
						{/if}
					</nav>
				</div>

				<!-- Tab Content -->
				<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
					{#if activeTab === 'actors'}
						{#each actors as character}
							<a
								href={character.peopleId ? `/person/${character.peopleId}` : '#'}
								class="text-center block hover:opacity-75 transition-opacity {character.peopleId ? 'cursor-pointer' : 'cursor-default'}"
							>
								<div class="aspect-square bg-gray-200 rounded-lg overflow-hidden mb-2">
									<img
										src={getCharacterImage(character)}
										alt={character.name || character.personName}
										class="w-full h-full object-cover"
										on:error={(e) => {
											e.currentTarget.src = 'https://via.placeholder.com/150x150?text=No+Image';
										}}
									/>
								</div>
								<p class="font-semibold text-sm text-gray-900 truncate" title={character.name}>
									{character.name || 'Unknown'}
								</p>
								{#if character.personName}
									<p class="text-xs text-gray-600 truncate" title={character.personName}>
										{character.personName}
									</p>
								{/if}
							</a>
						{/each}
					{:else if activeTab === 'directors'}
						{#each directors as character}
							<a
								href={character.peopleId ? `/person/${character.peopleId}` : '#'}
								class="text-center block hover:opacity-75 transition-opacity {character.peopleId ? 'cursor-pointer' : 'cursor-default'}"
							>
								<div class="aspect-square bg-gray-200 rounded-lg overflow-hidden mb-2">
									<img
										src={getCharacterImage(character)}
										alt={character.personName}
										class="w-full h-full object-cover"
										on:error={(e) => {
											e.currentTarget.src = 'https://via.placeholder.com/150x150?text=No+Image';
										}}
									/>
								</div>
								<p class="font-semibold text-sm text-gray-900 truncate" title={character.personName}>
									{character.personName || 'Unknown'}
								</p>
							</a>
						{/each}
					{:else if activeTab === 'writers'}
						{#each writers as character}
							<a
								href={character.peopleId ? `/person/${character.peopleId}` : '#'}
								class="text-center block hover:opacity-75 transition-opacity {character.peopleId ? 'cursor-pointer' : 'cursor-default'}"
							>
								<div class="aspect-square bg-gray-200 rounded-lg overflow-hidden mb-2">
									<img
										src={getCharacterImage(character)}
										alt={character.personName}
										class="w-full h-full object-cover"
										on:error={(e) => {
											e.currentTarget.src = 'https://via.placeholder.com/150x150?text=No+Image';
										}}
									/>
								</div>
								<p class="font-semibold text-sm text-gray-900 truncate" title={character.personName}>
									{character.personName || 'Unknown'}
								</p>
							</a>
						{/each}
					{:else if activeTab === 'producers'}
						{#each producers as character}
							<a
								href={character.peopleId ? `/person/${character.peopleId}` : '#'}
								class="text-center block hover:opacity-75 transition-opacity {character.peopleId ? 'cursor-pointer' : 'cursor-default'}"
							>
								<div class="aspect-square bg-gray-200 rounded-lg overflow-hidden mb-2">
									<img
										src={getCharacterImage(character)}
										alt={character.personName}
										class="w-full h-full object-cover"
										on:error={(e) => {
											e.currentTarget.src = 'https://via.placeholder.com/150x150?text=No+Image';
										}}
									/>
								</div>
								<p class="font-semibold text-sm text-gray-900 truncate" title={character.personName}>
									{character.personName || 'Unknown'}
								</p>
								<p class="text-xs text-gray-500">{character.peopleType}</p>
							</a>
						{/each}
					{:else if activeTab === 'other'}
						{#each otherCrew as character}
							<a
								href={character.peopleId ? `/person/${character.peopleId}` : '#'}
								class="text-center block hover:opacity-75 transition-opacity {character.peopleId ? 'cursor-pointer' : 'cursor-default'}"
							>
								<div class="aspect-square bg-gray-200 rounded-lg overflow-hidden mb-2">
									<img
										src={getCharacterImage(character)}
										alt={character.personName}
										class="w-full h-full object-cover"
										on:error={(e) => {
											e.currentTarget.src = 'https://via.placeholder.com/150x150?text=No+Image';
										}}
									/>
								</div>
								<p class="font-semibold text-sm text-gray-900 truncate" title={character.personName}>
									{character.personName || 'Unknown'}
								</p>
								{#if character.peopleType}
									<p class="text-xs text-gray-500">{character.peopleType}</p>
								{/if}
							</a>
						{/each}
					{/if}
				</div>
			</div>
		{/if}
	</div>
{/if}
