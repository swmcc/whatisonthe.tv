<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { goto } from '$app/navigation';
	import CheckInModal from '$lib/components/CheckInModal.svelte';

	let loading = true;
	let error = '';
	let data: any = null;
	let isSeries = true;
	let activeMainTab = 'cast-crew';
	let activeCrewTab = 'actors';
	let seasons: any[] = [];
	let loadingSeasons = false;
	let expandedSeasons = new Set<number>();
	let checkedInEpisodes = new Set<number>();

	// Check-in modal state
	let showCheckInModal = false;
	let checkInData: {
		contentId: number;
		contentName: string;
		contentType: 'series' | 'movie';
		episodeId: number | null;
		episodeName: string | null;
		seasonNumber: number | null;
		episodeNumber: number | null;
	} | null = null;

	const id = $page.params.id;

	onMount(async () => {
		await loadDetails();
	});

	async function loadDetails() {
		loading = true;
		error = '';

		// Check if URL has a type hint
		const typeHint = $page.url.searchParams.get('type');

		try {
			if (typeHint === 'movie') {
				// If explicitly told it's a movie, try movie first
				try {
					const response = await api.search.getMovie(parseInt(id));
					data = response;
					isSeries = false;
					return;
				} catch (movieError) {
					// Fall through to try series
				}
			}

			// Try series first (default behavior)
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

		// If it's a series, load seasons and check-ins
		if (isSeries && data) {
			await Promise.all([loadSeasons(), loadCheckins()]);
		}
	}

	async function loadCheckins() {
		try {
			const checkins = await api.checkin.listByContent(parseInt(id));
			// Build a set of episode IDs that have been checked in
			checkedInEpisodes = new Set(
				checkins
					.filter((c: any) => c.episode)
					.map((c: any) => c.episode.id)
			);
		} catch (e) {
			console.error('Failed to load check-ins:', e);
		}
	}

	async function loadSeasons() {
		loadingSeasons = true;
		try {
			const response = await api.search.getSeriesSeasons(parseInt(id));
			let seasonsList = response.seasons || [];

			// Sort seasons: regular seasons first (1, 2, 3...), then season 0 at the end
			seasonsList.sort((a, b) => {
				if (a.season_number === 0) return 1;
				if (b.season_number === 0) return -1;
				return a.season_number - b.season_number;
			});

			seasons = seasonsList;

			// Load episodes for each season
			for (const season of seasons) {
				const episodesResponse = await api.search.getSeasonEpisodes(parseInt(id), season.season_number);
				season.episodes = episodesResponse.episodes || [];
			}
		} catch (e) {
			console.error('Failed to load seasons:', e);
		} finally {
			loadingSeasons = false;
		}
	}

	function toggleSeason(seasonNumber: number) {
		if (expandedSeasons.has(seasonNumber)) {
			expandedSeasons.delete(seasonNumber);
		} else {
			expandedSeasons.add(seasonNumber);
		}
		expandedSeasons = expandedSeasons;
	}

	function openCheckInModal(episode: any = null, season: any = null) {
		if (!data) return;

		checkInData = {
			contentId: data.id,
			contentName: data.name || data.title,
			contentType: isSeries ? 'series' : 'movie',
			episodeId: episode?.id || null,
			episodeName: episode?.name || null,
			seasonNumber: episode?.season_number || season?.season_number || null,
			episodeNumber: episode?.episode_number || null
		};
		showCheckInModal = true;
	}

	function closeCheckInModal() {
		showCheckInModal = false;
		checkInData = null;
	}

	async function handleCheckInSuccess() {
		// Reload check-ins to update the UI
		console.log('Check-in successful!');
		if (isSeries) {
			await loadCheckins();
		}
	}

	const PLACEHOLDER_POSTER = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="500" height="750"%3E%3Crect fill="%23e5e7eb" width="500" height="750"/%3E%3Ctext fill="%236b7280" font-family="Arial" font-size="24" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3ENo Poster%3C/text%3E%3C/svg%3E';
	const PLACEHOLDER_PERSON = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="150" height="150"%3E%3Crect fill="%23e5e7eb" width="150" height="150"/%3E%3Ctext fill="%236b7280" font-family="Arial" font-size="16" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3ENo Image%3C/text%3E%3C/svg%3E';

	function getPosterUrl(imageUrl: string | null | undefined): string {
		if (!imageUrl) return PLACEHOLDER_POSTER;
		return imageUrl;
	}

	function getCharacterImage(character: any): string {
		if (character.image) return character.image;
		if (character.personImgURL) return character.personImgURL;
		return PLACEHOLDER_PERSON;
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
				<!-- Poster -->
				<div class="md:w-1/3 lg:w-1/4">
					<img
						src={getPosterUrl(data.image)}
						alt={data.name}
						class="w-full h-auto object-cover"
						on:error={(e) => {
							e.currentTarget.src = PLACEHOLDER_POSTER;
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

					<!-- Check-in Button -->
					<div class="mt-6">
						<button
							on:click={() => openCheckInModal()}
							class="w-full px-4 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors"
						>
							<svg class="w-5 h-5 inline-block mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
							</svg>
							Check In {isSeries ? 'Show' : 'Movie'}
						</button>
					</div>
				</div>
			</div>
		</div>

		<!-- Cast & Crew and Seasons -->
		{#if (data.characters && data.characters.length > 0) || (isSeries && seasons.length > 0)}
			{@const sortedCharacters = data.characters ? [...data.characters].sort((a, b) => (a.sort || 999) - (b.sort || 999)) : []}
			{@const actors = sortedCharacters.filter(c => c.peopleType === 'Actor')}
			{@const directors = sortedCharacters.filter(c => c.peopleType === 'Director')}
			{@const writers = sortedCharacters.filter(c => c.peopleType === 'Writer')}
			{@const producers = sortedCharacters.filter(c => c.peopleType === 'Executive Producer' || c.peopleType === 'Producer')}
			{@const otherCrew = sortedCharacters.filter(c => c.peopleType !== 'Actor' && c.peopleType !== 'Director' && c.peopleType !== 'Writer' && c.peopleType !== 'Executive Producer' && c.peopleType !== 'Producer')}

			<div class="bg-white rounded-lg shadow-lg p-6">
				<!-- Main Tabs -->
				<div class="border-b border-gray-200 mb-6">
					<nav class="-mb-px flex space-x-8">
						{#if data.characters && data.characters.length > 0}
							<button
								on:click={() => activeMainTab = 'cast-crew'}
								class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-base transition-colors
									{activeMainTab === 'cast-crew' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
							>
								Cast & Crew
							</button>
						{/if}
						{#if isSeries && seasons.length > 0}
							<button
								on:click={() => activeMainTab = 'seasons'}
								class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-base transition-colors
									{activeMainTab === 'seasons' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
							>
								Seasons ({seasons.length})
							</button>
						{/if}
					</nav>
				</div>

				<!-- Main Tab Content -->
				{#if activeMainTab === 'cast-crew'}
					<!-- Crew Sub-Tabs -->
					<div class="border-b border-gray-200 mb-6">
						<nav class="-mb-px flex space-x-8">
							{#if actors.length > 0}
								<button
									on:click={() => activeCrewTab = 'actors'}
									class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
										{activeCrewTab === 'actors' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
								>
									Cast ({actors.length})
								</button>
							{/if}
							{#if directors.length > 0}
								<button
									on:click={() => activeCrewTab = 'directors'}
									class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
										{activeCrewTab === 'directors' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
								>
									Directors ({directors.length})
								</button>
							{/if}
							{#if writers.length > 0}
								<button
									on:click={() => activeCrewTab = 'writers'}
									class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
										{activeCrewTab === 'writers' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
								>
									Writers ({writers.length})
								</button>
							{/if}
							{#if producers.length > 0}
								<button
									on:click={() => activeCrewTab = 'producers'}
									class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
										{activeCrewTab === 'producers' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
								>
									Producers ({producers.length})
								</button>
							{/if}
							{#if otherCrew.length > 0}
								<button
									on:click={() => activeCrewTab = 'other'}
									class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
										{activeCrewTab === 'other' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
								>
									Other ({otherCrew.length})
								</button>
							{/if}
						</nav>
					</div>

					<!-- Crew Content -->
					<div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3 sm:gap-4 md:gap-6">
						{#if activeCrewTab === 'actors'}
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
											e.currentTarget.src = PLACEHOLDER_PERSON;
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
					{:else if activeCrewTab === 'directors'}
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
											e.currentTarget.src = PLACEHOLDER_PERSON;
										}}
									/>
								</div>
								<p class="font-semibold text-sm text-gray-900 truncate" title={character.personName}>
									{character.personName || 'Unknown'}
								</p>
							</a>
						{/each}
					{:else if activeCrewTab === 'writers'}
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
											e.currentTarget.src = PLACEHOLDER_PERSON;
										}}
									/>
								</div>
								<p class="font-semibold text-sm text-gray-900 truncate" title={character.personName}>
									{character.personName || 'Unknown'}
								</p>
							</a>
						{/each}
					{:else if activeCrewTab === 'producers'}
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
											e.currentTarget.src = PLACEHOLDER_PERSON;
										}}
									/>
								</div>
								<p class="font-semibold text-sm text-gray-900 truncate" title={character.personName}>
									{character.personName || 'Unknown'}
								</p>
								<p class="text-xs text-gray-500">{character.peopleType}</p>
							</a>
						{/each}
					{:else if activeCrewTab === 'other'}
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
											e.currentTarget.src = PLACEHOLDER_PERSON;
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

				{:else if activeMainTab === 'seasons'}
					<!-- Seasons Tab -->
					{#if loadingSeasons}
						<div class="flex items-center justify-center py-8">
							<svg class="animate-spin h-8 w-8 text-indigo-600" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
						</div>
					{:else}
						<div class="space-y-4">
							{#each seasons as season}
								<div class="border border-gray-200 rounded-lg overflow-hidden">
									<!-- Season Header -->
									<button
										on:click={() => toggleSeason(season.season_number)}
										class="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between"
									>
										<div class="flex items-center gap-4">
											<div>
												<h3 class="text-lg font-semibold text-gray-900">
													{#if season.season_number === 0}
														Special Episodes
													{:else}
														Season {season.season_number}
													{/if}
													{#if season.name && season.name !== `Season ${season.season_number}` && season.season_number !== 0}
														<span class="text-gray-600">- {season.name}</span>
													{/if}
												</h3>
												{#if season.episodes}
													<p class="text-sm text-gray-600">{season.episodes.length} Episodes</p>
												{/if}
											</div>
										</div>
										<svg
											class="w-5 h-5 text-gray-500 transition-transform {expandedSeasons.has(season.season_number) ? 'rotate-180' : ''}"
											fill="none"
											viewBox="0 0 24 24"
											stroke="currentColor"
										>
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
										</svg>
									</button>

									<!-- Episodes List (Expanded) -->
									{#if expandedSeasons.has(season.season_number) && season.episodes}
										<div class="px-6 py-4 bg-white">
											<div class="space-y-3">
												{#each season.episodes as episode}
													<div class="flex gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors">
														<!-- Episode Image -->
														{#if episode.image || episode.image_url}
															<div class="flex-shrink-0 w-32 h-20 bg-gray-200 rounded overflow-hidden">
																<img
																	src={episode.image || episode.image_url}
																	alt={episode.name || `Episode ${episode.episode_number}`}
																	class="w-full h-full object-cover"
																	on:error={(e) => {
																		e.currentTarget.style.display = 'none';
																	}}
																/>
															</div>
														{/if}

														<!-- Episode Info -->
														<div class="flex-1 min-w-0">
															<div class="flex items-start justify-between gap-2">
																<div class="flex-1">
																	<h4 class="font-semibold text-gray-900">
																		{episode.episode_number}. {episode.name || 'TBA'}
																	</h4>
																	{#if episode.aired}
																		<p class="text-sm text-gray-500 mt-1">
																			Aired: {new Date(episode.aired).toLocaleDateString()}
																		</p>
																	{/if}
																</div>
																{#if episode.runtime}
																	<span class="text-sm text-gray-500 whitespace-nowrap">{episode.runtime} min</span>
																{/if}
															</div>
															{#if episode.overview}
																<p class="text-sm text-gray-600 mt-2 line-clamp-2">{episode.overview}</p>
															{/if}
														</div>

														<!-- Check-in Button -->
														<div class="flex-shrink-0">
															{@const isCheckedIn = checkedInEpisodes.has(episode.id)}
															<button
																on:click={() => openCheckInModal(episode, season)}
																class="px-3 py-2 text-sm font-medium rounded-md focus:outline-none focus:ring-2 transition-colors {isCheckedIn ? 'text-green-600 bg-green-50 hover:bg-green-100 focus:ring-green-500' : 'text-indigo-600 bg-indigo-50 hover:bg-indigo-100 focus:ring-indigo-500'}"
																title="{isCheckedIn ? 'Checked in - Click to check in again' : 'Check in this episode'}"
															>
																<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																	<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
																</svg>
															</button>
														</div>
													</div>
												{/each}
											</div>
										</div>
									{/if}
								</div>
							{/each}
						</div>
					{/if}
				{/if}
			</div>
		{/if}
	</div>
{/if}

<!-- Check-in Modal -->
{#if showCheckInModal && checkInData}
	<CheckInModal
		contentId={checkInData.contentId}
		contentName={checkInData.contentName}
		contentType={checkInData.contentType}
		episodeId={checkInData.episodeId}
		episodeName={checkInData.episodeName}
		seasonNumber={checkInData.seasonNumber}
		episodeNumber={checkInData.episodeNumber}
		on:close={closeCheckInModal}
		on:success={handleCheckInSuccess}
	/>
{/if}
