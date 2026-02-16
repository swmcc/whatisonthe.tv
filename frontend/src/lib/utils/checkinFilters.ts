/**
 * Checkin filtering utilities for advanced search functionality.
 */

export type FocusLevel = 'focused' | 'distracted' | 'background' | 'sleep';

export interface Checkin {
	id: number;
	watched_at: string;
	location?: string | null;
	watched_with?: string | null;
	notes?: string | null;
	focus?: FocusLevel | null;
	content?: {
		name?: string;
		content_type?: string;
	} | null;
	episode?: {
		name?: string;
	} | null;
}

export interface FilterOptions {
	searchQuery?: string;
	startDate?: string;
	endDate?: string;
	locations?: string[];
	people?: string[];
	mediaTypes?: string[];
	focusLevels?: string[];
}

// Media type labels mapping
export const MEDIA_TYPE_LABELS: Record<string, string> = {
	movie: 'Film',
	series: 'TV Series'
};

// Focus level labels mapping
export const FOCUS_LEVEL_LABELS: Record<FocusLevel, string> = {
	focused: 'Focused',
	distracted: 'Second Screening',
	background: 'Background',
	sleep: 'Sleep'
};

/**
 * Convert a display label back to content_type value.
 */
export function labelToContentType(label: string): string {
	for (const [type, displayLabel] of Object.entries(MEDIA_TYPE_LABELS)) {
		if (displayLabel === label) return type;
	}
	return label;
}

/**
 * Convert a content_type value to display label.
 */
export function contentTypeToLabel(contentType: string): string {
	return MEDIA_TYPE_LABELS[contentType] || contentType;
}

/**
 * Convert a display label back to focus level value.
 */
export function labelToFocusLevel(label: string): string {
	for (const [level, displayLabel] of Object.entries(FOCUS_LEVEL_LABELS)) {
		if (displayLabel === label) return level;
	}
	return label;
}

/**
 * Convert a focus level value to display label.
 */
export function focusLevelToLabel(focusLevel: string): string {
	return FOCUS_LEVEL_LABELS[focusLevel as FocusLevel] || focusLevel;
}

/**
 * Filter checkins by text search query.
 * Searches content name, episode name, location, watched_with, and notes.
 */
export function filterBySearchQuery(checkin: Checkin, query: string): boolean {
	if (!query) return true;

	const lowerQuery = query.toLowerCase();
	const contentName = checkin.content?.name?.toLowerCase() || '';
	const episodeName = checkin.episode?.name?.toLowerCase() || '';
	const location = checkin.location?.toLowerCase() || '';
	const watchedWith = checkin.watched_with?.toLowerCase() || '';
	const notes = checkin.notes?.toLowerCase() || '';

	return (
		contentName.includes(lowerQuery) ||
		episodeName.includes(lowerQuery) ||
		location.includes(lowerQuery) ||
		watchedWith.includes(lowerQuery) ||
		notes.includes(lowerQuery)
	);
}

/**
 * Filter checkins by date range.
 */
export function filterByDateRange(
	checkin: Checkin,
	startDate?: string,
	endDate?: string
): boolean {
	if (!startDate && !endDate) return true;

	const checkinDate = new Date(checkin.watched_at);
	checkinDate.setHours(0, 0, 0, 0);

	if (startDate) {
		const start = new Date(startDate);
		start.setHours(0, 0, 0, 0);
		if (checkinDate < start) return false;
	}

	if (endDate) {
		const end = new Date(endDate);
		end.setHours(23, 59, 59, 999);
		if (checkinDate > end) return false;
	}

	return true;
}

/**
 * Filter checkins by location.
 */
export function filterByLocations(checkin: Checkin, locations: string[]): boolean {
	if (!locations || locations.length === 0) return true;
	if (!checkin.location) return false;
	return locations.includes(checkin.location);
}

/**
 * Filter checkins by people (watched_with).
 */
export function filterByPeople(checkin: Checkin, people: string[]): boolean {
	if (!people || people.length === 0) return true;
	if (!checkin.watched_with) return false;
	return people.includes(checkin.watched_with);
}

/**
 * Filter checkins by media type (Film/TV Series).
 * Accepts display labels and converts them to content_type values.
 */
export function filterByMediaTypes(checkin: Checkin, mediaTypes: string[]): boolean {
	if (!mediaTypes || mediaTypes.length === 0) return true;

	const contentType = checkin.content?.content_type;
	if (!contentType) return false;

	const selectedContentTypes = mediaTypes.map(labelToContentType);
	return selectedContentTypes.includes(contentType);
}

/**
 * Filter checkins by focus level.
 * Accepts display labels and converts them to focus level values.
 */
export function filterByFocusLevels(checkin: Checkin, focusLevels: string[]): boolean {
	if (!focusLevels || focusLevels.length === 0) return true;

	const selectedFocusLevels = focusLevels.map(labelToFocusLevel);

	// Null/undefined focus is treated as 'focused' (full attention)
	const checkinFocus = checkin.focus || 'focused';
	return selectedFocusLevels.includes(checkinFocus);
}

/**
 * Apply all filters to a single checkin.
 */
export function applyFilters(checkin: Checkin, options: FilterOptions): boolean {
	if (!filterBySearchQuery(checkin, options.searchQuery || '')) return false;
	if (!filterByDateRange(checkin, options.startDate, options.endDate)) return false;
	if (!filterByLocations(checkin, options.locations || [])) return false;
	if (!filterByPeople(checkin, options.people || [])) return false;
	if (!filterByMediaTypes(checkin, options.mediaTypes || [])) return false;
	if (!filterByFocusLevels(checkin, options.focusLevels || [])) return false;
	return true;
}

/**
 * Filter an array of checkins based on filter options.
 */
export function filterCheckins(checkins: Checkin[], options: FilterOptions): Checkin[] {
	return checkins.filter((checkin) => applyFilters(checkin, options));
}

/**
 * Extract unique locations from checkins.
 */
export function extractUniqueLocations(checkins: Checkin[]): string[] {
	return [...new Set(checkins.map((c) => c.location).filter(Boolean) as string[])].sort();
}

/**
 * Extract unique people (watched_with) from checkins.
 */
export function extractUniquePeople(checkins: Checkin[]): string[] {
	return [...new Set(checkins.map((c) => c.watched_with).filter(Boolean) as string[])].sort();
}

/**
 * Extract unique media types from checkins and convert to display labels.
 */
export function extractUniqueMediaTypes(checkins: Checkin[]): string[] {
	const types = [
		...new Set(checkins.map((c) => c.content?.content_type).filter(Boolean) as string[])
	].sort();
	return types.map(contentTypeToLabel);
}

/**
 * Extract unique focus levels from checkins and convert to display labels.
 * Always includes 'Focused' since null/undefined focus means focused.
 */
export function extractUniqueFocusLevels(checkins: Checkin[]): string[] {
	const levels = new Set<string>();

	for (const checkin of checkins) {
		// Null/undefined focus is treated as 'focused'
		const focus = checkin.focus || 'focused';
		levels.add(focus);
	}

	// Sort by the order in FOCUS_LEVEL_LABELS
	const order: FocusLevel[] = ['focused', 'distracted', 'background', 'sleep'];
	const sortedLevels = [...levels].sort((a, b) => {
		return order.indexOf(a as FocusLevel) - order.indexOf(b as FocusLevel);
	});

	return sortedLevels.map(focusLevelToLabel);
}

/**
 * Group checkins by day.
 */
export function groupByDay(checkins: Checkin[]): Map<string, Checkin[]> {
	const groups = new Map<string, Checkin[]>();

	for (const checkin of checkins) {
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

/**
 * Check if any filters are active.
 */
export function hasActiveFilters(options: FilterOptions): boolean {
	return !!(
		options.searchQuery ||
		options.startDate ||
		options.endDate ||
		(options.locations && options.locations.length > 0) ||
		(options.people && options.people.length > 0) ||
		(options.mediaTypes && options.mediaTypes.length > 0) ||
		(options.focusLevels && options.focusLevels.length > 0)
	);
}
