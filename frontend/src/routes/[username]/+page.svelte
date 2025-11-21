<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';

	let username = '';
	let userInfo: any = null;
	let checkins: any[] = [];
	let loading = true;
	let loadingMore = false;
	let error = '';
	let hasMore = true;
	let oldestDate: string | null = null;
	let searchQuery = '';

	// Get username from URL
	$: username = $page.params.username;

	// Filter checkins based on search query
	$: filteredCheckins = searchQuery
		? checkins.filter((checkin) => {
				const query = searchQuery.toLowerCase();
				const contentName = checkin.content?.name?.toLowerCase() || '';
				const episodeName = checkin.episode?.name?.toLowerCase() || '';
				const location = checkin.location?.toLowerCase() || '';
				const watchedWith = checkin.watched_with?.toLowerCase() || '';
				const notes = checkin.notes?.toLowerCase() || '';

				return (
					contentName.includes(query) ||
					episodeName.includes(query) ||
					location.includes(query) ||
					watchedWith.includes(query) ||
					notes.includes(query)
				);
		  })
		: checkins;

	// Group filtered checkins by day
	$: groupedCheckins = groupByDay(filteredCheckins);

	// Redirect to login if clicking content links
	function handleContentClick(e: MouseEvent) {
		e.preventDefault();
		goto('/login');
	}

	onMount(async () => {
		try {
			userInfo = await api.auth.getPublicUser(username);
		} catch (err) {
			console.error('Failed to load user info:', err);
		}
		await loadCheckins();
		setupInfiniteScroll();
	});

	async function loadCheckins() {
		loading = true;
		error = '';

		try {
			const response = await api.checkin.listByUsername(username, 10);
			checkins = response;

			if (response.length > 0) {
				oldestDate = response[response.length - 1].watched_at;
			} else {
				hasMore = false;
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load check-ins';
		} finally {
			loading = false;
		}
	}

	async function loadMoreCheckins() {
		if (loadingMore || !hasMore || !oldestDate) return;

		loadingMore = true;
		try {
			const response = await api.checkin.listByUsername(username, 3, oldestDate);

			if (response.length === 0) {
				hasMore = false;
			} else {
				checkins = [...checkins, ...response];
				oldestDate = response[response.length - 1].watched_at;
			}
		} catch (err) {
			console.error('Failed to load more check-ins:', err);
		} finally {
			loadingMore = false;
		}
	}

	function setupInfiniteScroll() {
		const handleScroll = () => {
			const scrollTop = window.scrollY || document.documentElement.scrollTop;
			const scrollHeight = document.documentElement.scrollHeight;
			const clientHeight = document.documentElement.clientHeight;

			if (scrollHeight - scrollTop - clientHeight < 500 && hasMore && !loadingMore) {
				loadMoreCheckins();
			}
		};

		window.addEventListener('scroll', handleScroll);
		return () => window.removeEventListener('scroll', handleScroll);
	}

	function groupByDay(checkinList: any[]): Map<string, any[]> {
		const groups = new Map<string, any[]>();

		for (const checkin of checkinList) {
			const date = new Date(checkin.watched_at);
			const dayKey = date.toLocaleDateString('en-US', {
				year: 'numeric',
				month: 'long',
				day: 'numeric'
			});

			if (!groups.has(dayKey)) {
				groups.set(dayKey, []);
			}
			groups.get(dayKey)!.push(checkin);
		}

		return groups;
	}

	function formatEpisode(checkin: any) {
		if (checkin.episode) {
			const ep = checkin.episode;
			return `S${ep.season_number.toString().padStart(2, '0')}E${ep.episode_number.toString().padStart(2, '0')}`;
		}
		return null;
	}

	function formatDate(dateString: string) {
		const date = new Date(dateString);
		return date.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	const PLACEHOLDER_POSTER =
		'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="150"%3E%3Crect fill="%23e5e7eb" width="100" height="150"/%3E%3Ctext fill="%236b7280" font-family="Arial" font-size="12" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3ENo Poster%3C/text%3E%3C/svg%3E';
</script>

<svelte:head>
	<title>@{username} - Check-ins | What Is On The TV</title>
</svelte:head>

<div class="min-h-screen bg-gray-50">
	<!-- Header -->
	<nav class="bg-white shadow-sm">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex justify-between h-16">
				<div class="flex items-center gap-4">
					<!-- Retro TV Logo -->
					<svg width="40" height="40" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
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

					<div>
						{#if userInfo}
							<h1 class="text-2xl font-bold text-gray-900">
								{userInfo.first_name} {userInfo.last_name}
							</h1>
							<p class="text-sm text-indigo-600 font-medium">@{username}</p>
						{:else}
							<h1 class="text-2xl font-bold text-gray-900">@{username}</h1>
							<p class="text-sm text-gray-500">Public watch history</p>
						{/if}
					</div>
				</div>
				<div class="flex items-center">
					<a
						href="/login"
						class="text-sm font-medium text-indigo-600 hover:text-indigo-500 transition-colors"
					>
						Sign in to track your own
					</a>
				</div>
			</div>
		</div>
	</nav>

	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<div class="mb-8">
			<p class="text-gray-600">Public watch history for @{username}</p>

			<!-- Search Bar -->
			<div class="mt-4">
				<div class="relative">
					<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
						<svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
					</div>
					<input
						type="text"
						bind:value={searchQuery}
						placeholder="Search check-ins by title, episode, location, people, or notes..."
						class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
					/>
					{#if searchQuery}
						<div class="absolute inset-y-0 right-0 pr-3 flex items-center">
							<button
								on:click={() => searchQuery = ''}
								class="text-gray-400 hover:text-gray-600"
								title="Clear search"
							>
								<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						</div>
					{/if}
				</div>
				{#if searchQuery && filteredCheckins.length === 0 && !loading}
					<p class="mt-2 text-sm text-gray-500">
						No check-ins found matching "{searchQuery}"
					</p>
				{:else if searchQuery}
					<p class="mt-2 text-sm text-gray-500">
						Found {filteredCheckins.length} check-in{filteredCheckins.length !== 1 ? 's' : ''}
					</p>
				{/if}
			</div>
		</div>

		{#if loading}
			<div class="flex justify-center items-center py-12">
				<svg
					class="animate-spin h-8 w-8 text-indigo-600"
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
		{:else if error}
			<div class="p-4 bg-red-50 border-l-4 border-red-400 text-red-700">
				{error}
			</div>
		{:else if checkins.length === 0}
			<div class="text-center py-12">
				<svg
					class="mx-auto h-12 w-12 text-gray-400"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
					/>
				</svg>
				<h3 class="mt-2 text-sm font-medium text-gray-900">No check-ins yet</h3>
				<p class="mt-1 text-sm text-gray-500">
					@{username} hasn't logged any check-ins yet
				</p>
			</div>
		{:else}
			<div class="space-y-8">
				{#each Array.from(groupedCheckins.entries()) as [day, dayCheckins]}
					<!-- Day Header -->
					<div>
						<h2 class="text-lg font-semibold text-gray-900 mb-4 border-b border-gray-200 pb-2">
							{day}
						</h2>

						<!-- Checkins for this day -->
						<div class="space-y-4">
							{#each dayCheckins as checkin}
					<div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
						<div class="flex gap-4 p-4">
							<!-- Poster (non-clickable) -->
							<div class="flex-shrink-0">
								<img
									src={checkin.content.image_url || checkin.content.poster_url || PLACEHOLDER_POSTER}
									alt={checkin.content.name}
									class="w-24 h-36 object-cover rounded opacity-75"
									on:error={(e) => {
										e.currentTarget.src = PLACEHOLDER_POSTER;
									}}
								/>
							</div>

							<!-- Content Info -->
							<div class="flex-1 min-w-0">
								<div class="flex items-start justify-between">
									<div class="flex-1">
										<h3 class="text-xl font-bold text-gray-900">
											{checkin.content.name}
										</h3>
										{#if checkin.content.year}
											<span class="text-gray-500 ml-2">({checkin.content.year})</span>
										{/if}

										{#if checkin.episode}
											<p class="text-sm text-indigo-600 font-medium mt-1">
												{formatEpisode(checkin)}
												{#if checkin.episode.name}
													- {checkin.episode.name}
												{/if}
											</p>
										{/if}

										<div class="mt-3 space-y-2">
											<div class="flex items-center text-sm text-gray-600">
												<svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
													<path
														stroke-linecap="round"
														stroke-linejoin="round"
														stroke-width="2"
														d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
													/>
												</svg>
												{formatDate(checkin.watched_at)}
											</div>

											{#if checkin.location}
												<div class="flex items-center text-sm text-gray-600">
													<svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
														/>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
														/>
													</svg>
													{checkin.location}
												</div>
											{/if}

											{#if checkin.watched_with}
												<div class="flex items-center text-sm text-gray-600">
													<svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
														/>
													</svg>
													{checkin.watched_with}
												</div>
											{/if}

											{#if checkin.notes}
												<div class="mt-2 text-sm text-gray-700 italic">
													"{checkin.notes}"
												</div>
											{/if}
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				{/each}
						</div>
					</div>
				{/each}

				<!-- Loading More Indicator -->
				{#if loadingMore}
					<div class="flex justify-center items-center py-8">
						<svg
							class="animate-spin h-8 w-8 text-indigo-600"
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
				{/if}

				<!-- End of History Message -->
				{#if !hasMore && checkins.length > 0}
					<div class="text-center py-8 text-gray-500">
						<p>End of watch history</p>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>
