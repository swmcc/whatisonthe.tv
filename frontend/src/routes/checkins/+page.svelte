<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { api, AuthenticationError } from '$lib/api';
	import { auth } from '$lib/stores/auth';
	import DateFilter from '$lib/components/DateFilter.svelte';
	import MultiSelectFilter from '$lib/components/MultiSelectFilter.svelte';
	import CheckInModal from '$lib/components/CheckInModal.svelte';
	import SwansonModal from '$lib/components/SwansonModal.svelte';

	let checkins: any[] = [];
	let loading = true;
	let loadingMore = false;
	let error = '';
	let hasMore = true;
	let oldestDate: string | null = null;
	let searchQuery = '';
	let startDateFilter = '';
	let endDateFilter = '';
	let selectedLocations: string[] = [];
	let selectedPeople: string[] = [];
	let showEditModal = false;
	let editingCheckin: any = null;
	let showSwansonModal = false;

	// Extract unique locations and people from checkins
	$: uniqueLocations = [...new Set(checkins.map(c => c.location).filter(Boolean))].sort() as string[];
	$: uniquePeople = [...new Set(checkins.map(c => c.watched_with).filter(Boolean))].sort() as string[];

	// Clean up selected values if they're no longer valid options
	$: if (uniqueLocations.length > 0) {
		selectedLocations = selectedLocations.filter(s => uniqueLocations.includes(s));
	}
	$: if (uniquePeople.length > 0) {
		selectedPeople = selectedPeople.filter(s => uniquePeople.includes(s));
	}

	// Swanson button is only available when a date filter is applied
	$: showSwansonButton = startDateFilter !== '' || endDateFilter !== '';

	function openSwanson() {
		if (!showSwansonButton) return;
		showSwansonModal = true;
	}

	// Filter checkins based on search query, date range, location, and people
	$: filteredCheckins = checkins.filter((checkin) => {
		// Text search filter
		if (searchQuery) {
			const query = searchQuery.toLowerCase();
			const contentName = checkin.content?.name?.toLowerCase() || '';
			const episodeName = checkin.episode?.name?.toLowerCase() || '';
			const location = checkin.location?.toLowerCase() || '';
			const watchedWith = checkin.watched_with?.toLowerCase() || '';
			const notes = checkin.notes?.toLowerCase() || '';

			const matchesSearch =
				contentName.includes(query) ||
				episodeName.includes(query) ||
				location.includes(query) ||
				watchedWith.includes(query) ||
				notes.includes(query);

			if (!matchesSearch) return false;
		}

		// Date range filter
		if (startDateFilter || endDateFilter) {
			const checkinDate = new Date(checkin.watched_at);
			checkinDate.setHours(0, 0, 0, 0); // Normalize to start of day

			if (startDateFilter) {
				const startDate = new Date(startDateFilter);
				startDate.setHours(0, 0, 0, 0);
				if (checkinDate < startDate) return false;
			}

			if (endDateFilter) {
				const endDate = new Date(endDateFilter);
				endDate.setHours(23, 59, 59, 999); // End of day
				if (checkinDate > endDate) return false;
			}
		}

		// Location filter
		if (selectedLocations.length > 0) {
			if (!checkin.location || !selectedLocations.includes(checkin.location)) {
				return false;
			}
		}

		// People filter
		if (selectedPeople.length > 0) {
			if (!checkin.watched_with || !selectedPeople.includes(checkin.watched_with)) {
				return false;
			}
		}

		return true;
	});

	// Group filtered checkins by day
	$: groupedCheckins = groupByDay(filteredCheckins);

	onMount(async () => {
		// Restore filter state if coming back from Swanson
		if (browser) {
			const storedFilter = sessionStorage.getItem('swanson_filter');
			if (storedFilter) {
				const filter = JSON.parse(storedFilter);
				if (filter.startDate) startDateFilter = filter.startDate;
				if (filter.endDate) endDateFilter = filter.endDate;
			}
		}

		await loadCheckins();
		setupInfiniteScroll();
	});

	async function loadCheckins() {
		loading = true;
		error = '';

		// Ensure auth is valid before making API call
		if (!auth.isValid()) {
			goto('/login');
			return;
		}

		try {
			const response = await api.checkin.list(10); // Load last 10 days
			checkins = response;

			if (response.length > 0) {
				oldestDate = response[response.length - 1].watched_at;
			} else {
				hasMore = false;
			}
		} catch (err) {
			if (err instanceof AuthenticationError) {
				goto('/login');
				return;
			}
			error = err instanceof Error ? err.message : 'Failed to load check-ins';
		} finally {
			loading = false;
		}
	}

	async function loadMoreCheckins() {
		if (loadingMore || !hasMore || !oldestDate) return;

		loadingMore = true;
		try {
			const response = await api.checkin.list(3, oldestDate); // Load next 3 days

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

	async function deleteCheckin(id: number) {
		if (!confirm('Are you sure you want to delete this check-in?')) return;

		try {
			await api.checkin.delete(id);
			checkins = checkins.filter((c) => c.id !== id);
		} catch (err) {
			alert(err instanceof Error ? err.message : 'Failed to delete check-in');
		}
	}

	function openEditModal(checkin: any) {
		editingCheckin = checkin;
		showEditModal = true;
	}

	async function handleEditSuccess() {
		showEditModal = false;
		editingCheckin = null;
		// Reload checkins to reflect changes
		await loadCheckins();
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

	function handleDateFilterChange(event: CustomEvent<{ startDate: string; endDate: string }>) {
		startDateFilter = event.detail.startDate;
		endDateFilter = event.detail.endDate;
	}

	const PLACEHOLDER_POSTER =
		'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="150"%3E%3Crect fill="%23e5e7eb" width="100" height="150"/%3E%3Ctext fill="%236b7280" font-family="Arial" font-size="12" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3ENo Poster%3C/text%3E%3C/svg%3E';
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900">My Check-ins</h1>
		<p class="mt-2 text-gray-600">View your watching history</p>

		<!-- Date Filter -->
		<div class="mt-6">
			<DateFilter
				startDate={startDateFilter}
				endDate={endDateFilter}
				on:change={handleDateFilterChange}
			/>
		</div>

		<!-- Location & People Filters -->
		<div class="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
			<MultiSelectFilter
				label="Where"
				icon="location"
				options={uniqueLocations}
				bind:selected={selectedLocations}
				on:change={(e) => selectedLocations = e.detail.selected}
			/>
			<MultiSelectFilter
				label="Who"
				icon="people"
				options={uniquePeople}
				bind:selected={selectedPeople}
				on:change={(e) => selectedPeople = e.detail.selected}
			/>
		</div>

		<!-- Clear All Filters -->
		{#if searchQuery || startDateFilter || endDateFilter || selectedLocations.length > 0 || selectedPeople.length > 0}
			<div class="mt-3">
				<button
					on:click={() => {
						searchQuery = '';
						startDateFilter = '';
						endDateFilter = '';
						selectedLocations = [];
						selectedPeople = [];
					}}
					class="text-sm text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1"
				>
					<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
					Clear all filters
				</button>
			</div>
		{/if}

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
			{#if (searchQuery || startDateFilter || endDateFilter || selectedLocations.length > 0 || selectedPeople.length > 0) && filteredCheckins.length === 0 && !loading}
				<p class="mt-2 text-sm text-gray-500">
					No check-ins found matching your filters
				</p>
			{:else if searchQuery || startDateFilter || endDateFilter || selectedLocations.length > 0 || selectedPeople.length > 0}
				<p class="mt-2 text-sm text-gray-500">
					Found {filteredCheckins.length} check-in{filteredCheckins.length !== 1 ? 's' : ''}
					{#if searchQuery}
						matching "{searchQuery}"
					{/if}
					{#if startDateFilter || endDateFilter}
						{searchQuery ? ' in' : 'in'} selected date range
					{/if}
					{#if selectedLocations.length > 0}
						at {selectedLocations.length === 1 ? selectedLocations[0] : `${selectedLocations.length} locations`}
					{/if}
					{#if selectedPeople.length > 0}
						with {selectedPeople.length === 1 ? selectedPeople[0] : `${selectedPeople.length} people`}
					{/if}
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
				Start checking in movies and TV shows to build your watching history!
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
						<!-- Poster -->
						<a
							href={`/show/${checkin.content.tvdb_id}?type=${checkin.content.content_type}`}
							class="flex-shrink-0"
						>
							<img
								src={checkin.content.image_url || checkin.content.poster_url || PLACEHOLDER_POSTER}
								alt={checkin.content.name}
								class="w-24 h-36 object-cover rounded"
								on:error={(e) => {
									e.currentTarget.src = PLACEHOLDER_POSTER;
								}}
							/>
						</a>

						<!-- Content Info -->
						<div class="flex-1 min-w-0">
							<div class="flex items-start justify-between">
								<div class="flex-1">
									<a
										href={`/show/${checkin.content.tvdb_id}?type=${checkin.content.content_type}`}
										class="text-xl font-bold text-gray-900 hover:text-indigo-600 transition-colors"
									>
										{checkin.content.name}
									</a>
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

								<!-- Action Buttons -->
							<div class="ml-4 flex flex-col gap-1">
								<button
									on:click={() => openEditModal(checkin)}
									class="p-2 text-gray-500 hover:bg-gray-100 rounded-md transition-colors"
									title="Edit check-in"
								>
									<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
										/>
									</svg>
								</button>
								<button
									on:click={() => deleteCheckin(checkin.id)}
									class="p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors"
									title="Delete check-in"
								>
									<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
										/>
									</svg>
								</button>
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
					<p>You've reached the beginning of your watch history</p>
				</div>
			{/if}
		</div>
	{/if}
</div>

{#if showEditModal && editingCheckin}
	<CheckInModal
		mode="edit"
		checkinId={editingCheckin.id}
		contentId={editingCheckin.content.id}
		contentName={editingCheckin.content.name}
		contentType={editingCheckin.content.content_type}
		episodeId={editingCheckin.episode?.id || null}
		episodeName={editingCheckin.episode?.name || null}
		seasonNumber={editingCheckin.episode?.season_number || null}
		episodeNumber={editingCheckin.episode?.episode_number || null}
		existingData={{
			watched_at: editingCheckin.watched_at,
			location: editingCheckin.location,
			watched_with: editingCheckin.watched_with,
			notes: editingCheckin.notes
		}}
		on:success={handleEditSuccess}
		on:close={() => { showEditModal = false; editingCheckin = null; }}
	/>
{/if}

<!-- Swanson floating button - only appears when date filter is applied -->
{#if showSwansonButton && filteredCheckins.length > 0}
	<button
		on:click={openSwanson}
		class="fixed bottom-6 right-6 w-16 h-16 rounded-full shadow-lg hover:shadow-xl transition-all duration-200 overflow-hidden border-2 border-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 z-50 hover:scale-110"
		title="Ask Swanson for recommendations"
	>
		<img src="/swanson.png" alt="Ask Swanson" class="w-full h-full object-cover" />
	</button>
{/if}

<!-- Swanson Modal -->
{#if showSwansonModal}
	<SwansonModal
		checkins={filteredCheckins}
		filterInfo={{ startDate: startDateFilter, endDate: endDateFilter }}
		on:close={() => showSwansonModal = false}
	/>
{/if}
