<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { updates as updatesStore } from '$lib/stores/updates';
	import WatchlistButton from '$lib/components/WatchlistButton.svelte';

	let loading = true;
	let error = '';
	let items: any[] = [];
	let activeTab: 'content' | 'people' = 'content';

	// Subscribe to shared updates store
	$: updates = $updatesStore;

	const PLACEHOLDER_POSTER =
		'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="300" height="450"%3E%3Crect fill="%23e5e7eb" width="300" height="450"/%3E%3Ctext fill="%236b7280" font-family="Arial" font-size="20" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3ENo Poster%3C/text%3E%3C/svg%3E';
	const PLACEHOLDER_PERSON =
		'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="150" height="150"%3E%3Crect fill="%23e5e7eb" width="150" height="150"/%3E%3Ctext fill="%236b7280" font-family="Arial" font-size="16" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3ENo Image%3C/text%3E%3C/svg%3E';

	onMount(async () => {
		await loadWatchlist();
	});

	async function markAsRead(updateId: number) {
		await updatesStore.markAsRead(updateId);
	}

	async function markAllAsRead() {
		await updatesStore.markAllAsRead();
	}

	async function loadWatchlist() {
		loading = true;
		error = '';
		try {
			items = await api.watchlist.list();
		} catch (e: any) {
			error = e.message || 'Failed to load watchlist';
		} finally {
			loading = false;
		}
	}

	// Filter items based on active tab
	$: contentItems = items.filter((i) => i.item_type === 'content');
	$: peopleItems = items.filter((i) => i.item_type === 'person');

	// Get current items based on tab
	$: currentItems = activeTab === 'content' ? contentItems : peopleItems;

	function getPosterUrl(content: any): string {
		return content?.image_url || content?.poster_url || PLACEHOLDER_POSTER;
	}

	function getPersonImage(person: any): string {
		return person?.image_url || PLACEHOLDER_PERSON;
	}

	function handleRemoved(event: CustomEvent) {
		// Remove item from local list
		const { type, id } = event.detail;
		items = items.filter((item) => {
			if (type === 'content') {
				return !(item.item_type === 'content' && item.content?.tvdb_id === id);
			} else {
				return !(item.item_type === 'person' && item.person?.tvdb_id === id);
			}
		});
	}

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function formatRelativeTime(dateStr: string): string {
		const date = new Date(dateStr);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffMins = Math.floor(diffMs / 60000);
		const diffHours = Math.floor(diffMs / 3600000);
		const diffDays = Math.floor(diffMs / 86400000);

		if (diffMins < 60) return `${diffMins}m ago`;
		if (diffHours < 24) return `${diffHours}h ago`;
		if (diffDays < 7) return `${diffDays}d ago`;
		return formatDate(dateStr);
	}

	function getUpdateTypeLabel(type: string): string {
		const labels: Record<string, string> = {
			status_change: 'Status Change',
			new_episode: 'New Episode',
			new_cast: 'New Cast',
			metadata_update: 'Updated'
		};
		return labels[type] || type;
	}

	function getUpdateTypeColor(type: string): string {
		const colors: Record<string, string> = {
			status_change: 'bg-amber-100 text-amber-800',
			new_episode: 'bg-green-100 text-green-800',
			new_cast: 'bg-blue-100 text-blue-800',
			metadata_update: 'bg-gray-100 text-gray-800'
		};
		return colors[type] || 'bg-gray-100 text-gray-800';
	}

	$: unreadCount = updates.length;
</script>

<svelte:head>
	<title>Watchlist - What Is On The TV</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 py-8">
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900">Watchlist</h1>
		<p class="mt-2 text-gray-600">Keep track of shows, movies, and people you want to follow.</p>
	</div>

	<!-- News Section -->
	{#if updates.length > 0}
		<div class="mb-8 bg-white rounded-lg shadow-lg overflow-hidden">
			<div class="px-6 py-4 bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-between">
				<div class="flex items-center space-x-2">
					<svg class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
					</svg>
					<h2 class="text-lg font-semibold text-white">News</h2>
					{#if unreadCount > 0}
						<span class="px-2 py-0.5 bg-white/20 rounded-full text-sm text-white">
							{unreadCount} new
						</span>
					{/if}
				</div>
				{#if unreadCount > 0}
					<button
						on:click={markAllAsRead}
						class="text-sm text-white/80 hover:text-white transition-colors"
					>
						Mark all as read
					</button>
				{/if}
			</div>
			<div class="divide-y divide-gray-100">
				{#each updates as update}
					<div
						class="px-6 py-4 flex items-start space-x-4 hover:bg-gray-50 transition-colors"
					>
						<!-- Content/Person image -->
						<div class="flex-shrink-0">
							{#if update.watchlist_item?.content}
								<a href="/show/{update.watchlist_item.content.tvdb_id}">
									<img
										src={update.watchlist_item.content.image_url || update.watchlist_item.content.poster_url || PLACEHOLDER_POSTER}
										alt={update.watchlist_item.content.name}
										class="h-16 w-12 object-cover rounded"
									/>
								</a>
							{:else if update.watchlist_item?.person}
								<a href="/person/{update.watchlist_item.person.tvdb_id}">
									<img
										src={update.watchlist_item.person.image_url || PLACEHOLDER_PERSON}
										alt={update.watchlist_item.person.full_name}
										class="h-12 w-12 object-cover rounded-full"
									/>
								</a>
							{:else}
								<div class="h-16 w-12 bg-gray-200 rounded flex items-center justify-center">
									<svg class="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
									</svg>
								</div>
							{/if}
						</div>

						<!-- Update content -->
						<div class="flex-1 min-w-0">
							<div class="flex items-center space-x-2">
								<span class="text-xs px-2 py-0.5 rounded-full font-medium {getUpdateTypeColor(update.update_type)}">
									{getUpdateTypeLabel(update.update_type)}
								</span>
								<span class="text-xs text-gray-400">{formatRelativeTime(update.created_at)}</span>
							</div>
							<p class="mt-1 text-sm text-gray-900">{update.description}</p>
							{#if update.watchlist_item?.content}
								<a
									href="/show/{update.watchlist_item.content.tvdb_id}"
									class="mt-1 text-xs text-indigo-600 hover:text-indigo-800"
								>
									{update.watchlist_item.content.name}
								</a>
							{:else if update.watchlist_item?.person}
								<a
									href="/person/{update.watchlist_item.person.tvdb_id}"
									class="mt-1 text-xs text-indigo-600 hover:text-indigo-800"
								>
									{update.watchlist_item.person.full_name}
								</a>
							{/if}
						</div>

						<!-- Mark as read button -->
						{#if !update.is_read}
							<button
								on:click={() => markAsRead(update.id)}
								class="flex-shrink-0 p-1 text-gray-400 hover:text-indigo-600 transition-colors"
								title="Mark as read"
							>
								<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
								</svg>
							</button>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{/if}

	{#if loading}
		<div class="flex items-center justify-center min-h-[50vh]">
			<div class="text-center">
				<svg class="animate-spin h-12 w-12 text-indigo-600 mx-auto" viewBox="0 0 24 24">
					<circle
						class="opacity-25"
						cx="12"
						cy="12"
						r="10"
						stroke="currentColor"
						stroke-width="4"
						fill="none"
					></circle>
					<path
						class="opacity-75"
						fill="currentColor"
						d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
					></path>
				</svg>
				<p class="mt-4 text-gray-600">Loading watchlist...</p>
			</div>
		</div>
	{:else if error}
		<div class="bg-red-50 border-l-4 border-red-500 p-4 rounded">
			<p class="text-sm text-red-700">{error}</p>
			<button on:click={loadWatchlist} class="mt-4 text-indigo-600 hover:text-indigo-800">
				Try again
			</button>
		</div>
	{:else}
		<div class="bg-white rounded-lg shadow-lg">
			<!-- Tabs -->
			<div class="border-b border-gray-200">
				<nav class="flex -mb-px px-6">
					<button
						on:click={() => (activeTab = 'content')}
						class="whitespace-nowrap py-4 px-4 border-b-2 font-medium text-sm transition-colors
							{activeTab === 'content'
							? 'border-indigo-500 text-indigo-600'
							: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
					>
						Shows & Movies ({contentItems.length})
					</button>
					<button
						on:click={() => (activeTab = 'people')}
						class="whitespace-nowrap py-4 px-4 border-b-2 font-medium text-sm transition-colors
							{activeTab === 'people'
							? 'border-indigo-500 text-indigo-600'
							: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
					>
						People ({peopleItems.length})
					</button>
				</nav>
			</div>

			<!-- Content -->
			<div class="p-6">
				{#if currentItems.length === 0}
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
								d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
							/>
						</svg>
						<h3 class="mt-2 text-sm font-medium text-gray-900">No items yet</h3>
						<p class="mt-1 text-sm text-gray-500">
							{#if activeTab === 'content'}
								Start adding shows and movies to your watchlist.
							{:else}
								Follow people to keep track of their new work.
							{/if}
						</p>
						<div class="mt-6">
							<a
								href="/"
								class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
							>
								<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
									/>
								</svg>
								Search for content
							</a>
						</div>
					</div>
				{:else if activeTab === 'content'}
					<!-- Content Grid -->
					<div
						class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4"
					>
						{#each currentItems as item}
							{@const content = item.content}
							{#if content}
								<div class="group relative">
									<a
										href="/show/{content.tvdb_id}{content.content_type === 'movie' ? '?type=movie' : ''}"
										class="block bg-white rounded-lg shadow hover:shadow-lg transition-shadow"
									>
										<div class="aspect-[2/3] bg-gray-200 rounded-t-lg overflow-hidden">
											<img
												src={getPosterUrl(content)}
												alt={content.name}
												class="w-full h-full object-cover"
												on:error={(e) => {
													e.currentTarget.src = PLACEHOLDER_POSTER;
												}}
											/>
										</div>
										<div class="p-3">
											<h3 class="font-semibold text-gray-900 text-sm truncate" title={content.name}>
												{content.name}
											</h3>
											<div class="flex items-center justify-between mt-1">
												<span class="text-xs text-gray-500">{content.year || 'N/A'}</span>
												<span
													class="text-xs px-2 py-0.5 rounded-full {content.content_type === 'movie'
														? 'bg-purple-100 text-purple-700'
														: 'bg-blue-100 text-blue-700'}"
												>
													{content.content_type === 'movie' ? 'Movie' : 'Series'}
												</span>
											</div>
											<p class="text-xs text-gray-400 mt-2">
												Added {formatDate(item.created_at)}
											</p>
										</div>
									</a>
									<!-- Remove button (appears on hover) -->
									<div
										class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
									>
										<WatchlistButton
											type="content"
											id={content.tvdb_id}
											compact={true}
											on:removed={handleRemoved}
										/>
									</div>
								</div>
							{/if}
						{/each}
					</div>
				{:else}
					<!-- Person Grid (Actors or Directors) -->
					<div
						class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4"
					>
						{#each currentItems as item}
							{@const person = item.person}
							{#if person}
								<div class="group relative">
									<a
										href="/person/{person.tvdb_id}"
										class="block bg-white rounded-lg shadow hover:shadow-lg transition-shadow text-center"
									>
										<div class="aspect-square bg-gray-200 rounded-t-lg overflow-hidden">
											<img
												src={getPersonImage(person)}
												alt={person.full_name}
												class="w-full h-full object-cover"
												on:error={(e) => {
													e.currentTarget.src = PLACEHOLDER_PERSON;
												}}
											/>
										</div>
										<div class="p-3">
											<h3
												class="font-semibold text-gray-900 text-sm truncate"
												title={person.full_name}
											>
												{person.full_name}
											</h3>
											{#if item.person_role_filter && item.person_role_filter !== 'any'}
												<span class="text-xs text-indigo-600 capitalize">
													{item.person_role_filter}
												</span>
											{/if}
											<p class="text-xs text-gray-400 mt-2">
												Added {formatDate(item.created_at)}
											</p>
										</div>
									</a>
									<!-- Remove button (appears on hover) -->
									<div
										class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
									>
										<WatchlistButton
											type="person"
											id={person.tvdb_id}
											compact={true}
											on:removed={handleRemoved}
										/>
									</div>
								</div>
							{/if}
						{/each}
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
