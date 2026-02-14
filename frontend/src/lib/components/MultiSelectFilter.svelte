<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let label: string;
	export let icon: 'location' | 'people' | 'media' = 'location';
	export let options: string[] = [];
	export let selected: string[] = [];

	const dispatch = createEventDispatcher();

	let isOpen = false;

	function toggleOption(option: string) {
		if (selected.includes(option)) {
			selected = selected.filter(s => s !== option);
		} else {
			selected = [...selected, option];
		}
		dispatch('change', { selected });
	}

	function clearAll() {
		selected = [];
		dispatch('change', { selected });
	}

	function selectAll() {
		selected = [...options];
		dispatch('change', { selected });
	}

	// Close dropdown when clicking outside
	function handleClickOutside(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (!target.closest('.multi-select-container')) {
			isOpen = false;
		}
	}
</script>

<svelte:window on:click={handleClickOutside} />

<div class="multi-select-container relative">
	<button
		type="button"
		on:click|stopPropagation={() => isOpen = !isOpen}
		class="w-full px-3 py-2 text-sm font-medium rounded-lg transition-all flex items-center justify-between gap-2
			{selected.length > 0
				? 'bg-indigo-50 text-indigo-700 border-2 border-indigo-300'
				: 'bg-gray-50 text-gray-700 hover:bg-gray-100 border-2 border-gray-200'}"
	>
		<span class="flex items-center gap-2">
			{#if icon === 'location'}
				<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
				</svg>
			{:else if icon === 'people'}
				<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
				</svg>
			{:else}
				<!-- media icon (film/tv) -->
				<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
				</svg>
			{/if}
			<span class="truncate">
				{#if selected.length === 0}
					{label}
				{:else if selected.length === 1}
					{selected[0]}
				{:else}
					{selected.length} selected
				{/if}
			</span>
		</span>
		<svg
			class="w-4 h-4 transform transition-transform flex-shrink-0 {isOpen ? 'rotate-180' : ''}"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
		>
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
		</svg>
	</button>

	{#if isOpen && options.length > 0}
		<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
		<div
			class="absolute z-50 mt-1 w-full bg-white rounded-lg shadow-lg border border-gray-200 py-1 max-h-60 overflow-auto"
			on:click|stopPropagation
		>
			<!-- Select All / Clear -->
			<div class="px-3 py-2 border-b border-gray-100 flex justify-between">
				<button
					type="button"
					on:click={selectAll}
					class="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
				>
					Select All
				</button>
				<button
					type="button"
					on:click={clearAll}
					class="text-xs text-gray-500 hover:text-gray-700 font-medium"
				>
					Clear
				</button>
			</div>

			<!-- Options -->
			{#each options as option}
				<button
					type="button"
					on:click={() => toggleOption(option)}
					class="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
				>
					<span class="w-4 h-4 rounded border flex-shrink-0 flex items-center justify-center
						{selected.includes(option) ? 'bg-indigo-600 border-indigo-600' : 'border-gray-300'}">
						{#if selected.includes(option)}
							<svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
								<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
							</svg>
						{/if}
					</span>
					<span class="truncate">{option}</span>
				</button>
			{/each}
		</div>
	{/if}

	{#if options.length === 0}
		<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
		<div class="absolute inset-0 cursor-not-allowed" on:click|stopPropagation></div>
	{/if}
</div>
