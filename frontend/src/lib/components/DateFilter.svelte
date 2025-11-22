<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let startDate: string = '';
	export let endDate: string = '';

	const dispatch = createEventDispatcher();

	type FilterMode = 'day' | 'week' | 'month' | 'range' | 'all';
	let mode: FilterMode = 'all';
	let showCalendar = false;

	// Format date to YYYY-MM-DD
	function formatDate(date: Date): string {
		return date.toISOString().split('T')[0];
	}

	// Get today's date
	function getToday(): string {
		return formatDate(new Date());
	}

	// Get start of week (Monday)
	function getStartOfWeek(date: Date): string {
		const d = new Date(date);
		const day = d.getDay();
		const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
		return formatDate(new Date(d.setDate(diff)));
	}

	// Get end of week (Sunday)
	function getEndOfWeek(date: Date): string {
		const d = new Date(date);
		const day = d.getDay();
		const diff = d.getDate() + (day === 0 ? 0 : 7 - day);
		return formatDate(new Date(d.setDate(diff)));
	}

	// Get start of month
	function getStartOfMonth(date: Date): string {
		return formatDate(new Date(date.getFullYear(), date.getMonth(), 1));
	}

	// Get end of month
	function getEndOfMonth(date: Date): string {
		return formatDate(new Date(date.getFullYear(), date.getMonth() + 1, 0));
	}

	function applyFilter(newMode: FilterMode) {
		mode = newMode;
		const today = new Date();

		switch (mode) {
			case 'day':
				startDate = getToday();
				endDate = getToday();
				break;
			case 'week':
				startDate = getStartOfWeek(today);
				endDate = getEndOfWeek(today);
				break;
			case 'month':
				startDate = getStartOfMonth(today);
				endDate = getEndOfMonth(today);
				break;
			case 'all':
				startDate = '';
				endDate = '';
				break;
			case 'range':
				// Keep existing values or set to current month
				if (!startDate) startDate = getStartOfMonth(today);
				if (!endDate) endDate = getEndOfMonth(today);
				break;
		}

		dispatch('change', { startDate, endDate });
	}

	function handleDateChange() {
		if (mode === 'range') {
			dispatch('change', { startDate, endDate });
		}
	}

	function clearFilter() {
		mode = 'all';
		startDate = '';
		endDate = '';
		dispatch('change', { startDate: '', endDate: '' });
	}

	// Format date for display
	function formatDisplayDate(dateStr: string): string {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
	}
</script>

<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
	<div class="flex items-center justify-between mb-4">
		<h3 class="text-sm font-semibold text-gray-900 uppercase tracking-wide">Date Filter</h3>
		{#if mode !== 'all'}
			<button
				on:click={clearFilter}
				class="text-xs text-indigo-600 hover:text-indigo-800 font-medium transition-colors"
			>
				Clear Filter
			</button>
		{/if}
	</div>

	<!-- Quick Filter Buttons -->
	<div class="grid grid-cols-4 gap-2 mb-4">
		<button
			on:click={() => applyFilter('all')}
			class="px-3 py-2 text-sm font-medium rounded-md transition-all {mode === 'all'
				? 'bg-indigo-600 text-white shadow-sm'
				: 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
		>
			All Time
		</button>
		<button
			on:click={() => applyFilter('day')}
			class="px-3 py-2 text-sm font-medium rounded-md transition-all {mode === 'day'
				? 'bg-indigo-600 text-white shadow-sm'
				: 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
		>
			Today
		</button>
		<button
			on:click={() => applyFilter('week')}
			class="px-3 py-2 text-sm font-medium rounded-md transition-all {mode === 'week'
				? 'bg-indigo-600 text-white shadow-sm'
				: 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
		>
			This Week
		</button>
		<button
			on:click={() => applyFilter('month')}
			class="px-3 py-2 text-sm font-medium rounded-md transition-all {mode === 'month'
				? 'bg-indigo-600 text-white shadow-sm'
				: 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
		>
			This Month
		</button>
	</div>

	<!-- Custom Range Toggle -->
	<button
		on:click={() => {
			showCalendar = !showCalendar;
			if (!showCalendar) {
				mode = 'all';
				clearFilter();
			} else {
				applyFilter('range');
			}
		}}
		class="w-full px-4 py-2.5 text-sm font-medium rounded-md transition-all flex items-center justify-between {showCalendar
			? 'bg-indigo-50 text-indigo-700 border-2 border-indigo-600'
			: 'bg-gray-50 text-gray-700 hover:bg-gray-100 border-2 border-gray-200'}"
	>
		<span class="flex items-center gap-2">
			<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
				/>
			</svg>
			Custom Date Range
		</span>
		<svg
			class="w-5 h-5 transform transition-transform {showCalendar ? 'rotate-180' : ''}"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
		>
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
		</svg>
	</button>

	<!-- Custom Date Range Inputs -->
	{#if showCalendar}
		<div class="mt-4 p-4 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg border border-indigo-100 space-y-4">
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<!-- Start Date -->
				<div>
					<label for="start-date" class="block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
						Start Date
					</label>
					<div class="relative">
						<input
							id="start-date"
							type="date"
							bind:value={startDate}
							on:change={handleDateChange}
							max={endDate || undefined}
							class="w-full px-3 py-2.5 border-2 border-indigo-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all bg-white"
						/>
						<div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
							<svg class="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
								/>
							</svg>
						</div>
					</div>
				</div>

				<!-- End Date -->
				<div>
					<label for="end-date" class="block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
						End Date
					</label>
					<div class="relative">
						<input
							id="end-date"
							type="date"
							bind:value={endDate}
							on:change={handleDateChange}
							min={startDate || undefined}
							class="w-full px-3 py-2.5 border-2 border-indigo-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all bg-white"
						/>
						<div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
							<svg class="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
								/>
							</svg>
						</div>
					</div>
				</div>
			</div>

			<!-- Selected Range Display -->
			{#if startDate && endDate}
				<div class="text-center pt-2 border-t border-indigo-200">
					<p class="text-xs font-medium text-indigo-700">
						Showing check-ins from
						<span class="font-bold">{formatDisplayDate(startDate)}</span>
						to
						<span class="font-bold">{formatDisplayDate(endDate)}</span>
					</p>
				</div>
			{/if}
		</div>
	{/if}

	<!-- Active Filter Summary -->
	{#if mode !== 'all' && !showCalendar}
		<div class="mt-3 text-center">
			<p class="text-xs text-gray-600">
				{#if mode === 'day'}
					Showing check-ins for <span class="font-semibold text-indigo-600">today</span>
				{:else if mode === 'week'}
					Showing check-ins for <span class="font-semibold text-indigo-600">this week</span>
				{:else if mode === 'month'}
					Showing check-ins for <span class="font-semibold text-indigo-600">this month</span>
				{/if}
			</p>
		</div>
	{/if}
</div>
