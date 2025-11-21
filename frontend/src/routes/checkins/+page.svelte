<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { goto } from '$app/navigation';

	let checkins: any[] = [];
	let loading = true;
	let error = '';

	onMount(async () => {
		await loadCheckins();
	});

	async function loadCheckins() {
		loading = true;
		error = '';

		try {
			const response = await api.checkin.list(100, 0);
			checkins = response;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load check-ins';
		} finally {
			loading = false;
		}
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

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900">My Check-ins</h1>
		<p class="mt-2 text-gray-600">View your watching history</p>
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
		<div class="space-y-4">
			{#each checkins as checkin}
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

								<!-- Delete Button -->
								<button
									on:click={() => deleteCheckin(checkin.id)}
									class="ml-4 p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors"
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
			{/each}
		</div>
	{/if}
</div>
