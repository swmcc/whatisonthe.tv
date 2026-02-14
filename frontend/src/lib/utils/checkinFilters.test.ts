import { describe, it, expect } from 'vitest';
import {
	filterBySearchQuery,
	filterByDateRange,
	filterByLocations,
	filterByPeople,
	filterByMediaTypes,
	applyFilters,
	filterCheckins,
	extractUniqueLocations,
	extractUniquePeople,
	extractUniqueMediaTypes,
	groupByDay,
	hasActiveFilters,
	labelToContentType,
	contentTypeToLabel,
	type Checkin,
	type FilterOptions
} from './checkinFilters';

// Test data factory
function createCheckin(overrides: Partial<Checkin> = {}): Checkin {
	return {
		id: 1,
		watched_at: '2024-01-15T20:00:00Z',
		location: 'Home',
		watched_with: 'Family',
		notes: 'Great show!',
		content: {
			name: 'Breaking Bad',
			content_type: 'series'
		},
		episode: {
			name: 'Pilot'
		},
		...overrides
	};
}

describe('labelToContentType', () => {
	it('converts Film to movie', () => {
		expect(labelToContentType('Film')).toBe('movie');
	});

	it('converts TV Series to series', () => {
		expect(labelToContentType('TV Series')).toBe('series');
	});

	it('returns unknown labels unchanged', () => {
		expect(labelToContentType('Documentary')).toBe('Documentary');
	});
});

describe('contentTypeToLabel', () => {
	it('converts movie to Film', () => {
		expect(contentTypeToLabel('movie')).toBe('Film');
	});

	it('converts series to TV Series', () => {
		expect(contentTypeToLabel('series')).toBe('TV Series');
	});

	it('returns unknown types unchanged', () => {
		expect(contentTypeToLabel('documentary')).toBe('documentary');
	});
});

describe('filterBySearchQuery', () => {
	it('returns true when query is empty', () => {
		const checkin = createCheckin();
		expect(filterBySearchQuery(checkin, '')).toBe(true);
	});

	it('matches content name', () => {
		const checkin = createCheckin({ content: { name: 'The Office', content_type: 'series' } });
		expect(filterBySearchQuery(checkin, 'office')).toBe(true);
		expect(filterBySearchQuery(checkin, 'Office')).toBe(true);
		expect(filterBySearchQuery(checkin, 'parks')).toBe(false);
	});

	it('matches episode name', () => {
		const checkin = createCheckin({ episode: { name: 'The Pilot Episode' } });
		expect(filterBySearchQuery(checkin, 'pilot')).toBe(true);
		expect(filterBySearchQuery(checkin, 'finale')).toBe(false);
	});

	it('matches location', () => {
		const checkin = createCheckin({ location: 'Cinema' });
		expect(filterBySearchQuery(checkin, 'cinema')).toBe(true);
		expect(filterBySearchQuery(checkin, 'home')).toBe(false);
	});

	it('matches watched_with', () => {
		const checkin = createCheckin({ watched_with: 'John and Sarah' });
		expect(filterBySearchQuery(checkin, 'sarah')).toBe(true);
		expect(filterBySearchQuery(checkin, 'mike')).toBe(false);
	});

	it('matches notes', () => {
		const checkin = createCheckin({ notes: 'Amazing cinematography' });
		expect(filterBySearchQuery(checkin, 'cinematography')).toBe(true);
		expect(filterBySearchQuery(checkin, 'boring')).toBe(false);
	});

	it('is case insensitive', () => {
		const checkin = createCheckin({ content: { name: 'Breaking Bad', content_type: 'series' } });
		expect(filterBySearchQuery(checkin, 'BREAKING')).toBe(true);
		expect(filterBySearchQuery(checkin, 'breaking')).toBe(true);
		expect(filterBySearchQuery(checkin, 'BrEaKiNg')).toBe(true);
	});

	it('handles null/undefined fields gracefully', () => {
		const checkin = createCheckin({
			content: null,
			episode: null,
			location: null,
			watched_with: null,
			notes: null
		});
		expect(filterBySearchQuery(checkin, 'test')).toBe(false);
	});
});

describe('filterByDateRange', () => {
	const checkin = createCheckin({ watched_at: '2024-01-15T20:00:00Z' });

	it('returns true when no date range is specified', () => {
		expect(filterByDateRange(checkin, undefined, undefined)).toBe(true);
	});

	it('filters by start date', () => {
		expect(filterByDateRange(checkin, '2024-01-01', undefined)).toBe(true);
		expect(filterByDateRange(checkin, '2024-01-15', undefined)).toBe(true);
		expect(filterByDateRange(checkin, '2024-01-16', undefined)).toBe(false);
	});

	it('filters by end date', () => {
		expect(filterByDateRange(checkin, undefined, '2024-01-31')).toBe(true);
		expect(filterByDateRange(checkin, undefined, '2024-01-15')).toBe(true);
		expect(filterByDateRange(checkin, undefined, '2024-01-14')).toBe(false);
	});

	it('filters by date range', () => {
		expect(filterByDateRange(checkin, '2024-01-01', '2024-01-31')).toBe(true);
		expect(filterByDateRange(checkin, '2024-01-15', '2024-01-15')).toBe(true);
		expect(filterByDateRange(checkin, '2024-01-16', '2024-01-31')).toBe(false);
		expect(filterByDateRange(checkin, '2024-01-01', '2024-01-14')).toBe(false);
	});
});

describe('filterByLocations', () => {
	it('returns true when locations array is empty', () => {
		const checkin = createCheckin({ location: 'Home' });
		expect(filterByLocations(checkin, [])).toBe(true);
	});

	it('returns false when checkin has no location', () => {
		const checkin = createCheckin({ location: null });
		expect(filterByLocations(checkin, ['Home'])).toBe(false);
	});

	it('matches single location', () => {
		const checkin = createCheckin({ location: 'Home' });
		expect(filterByLocations(checkin, ['Home'])).toBe(true);
		expect(filterByLocations(checkin, ['Cinema'])).toBe(false);
	});

	it('matches multiple locations', () => {
		const checkin = createCheckin({ location: 'Cinema' });
		expect(filterByLocations(checkin, ['Home', 'Cinema', 'Work'])).toBe(true);
		expect(filterByLocations(checkin, ['Home', 'Work'])).toBe(false);
	});
});

describe('filterByPeople', () => {
	it('returns true when people array is empty', () => {
		const checkin = createCheckin({ watched_with: 'Family' });
		expect(filterByPeople(checkin, [])).toBe(true);
	});

	it('returns false when checkin has no watched_with', () => {
		const checkin = createCheckin({ watched_with: null });
		expect(filterByPeople(checkin, ['Family'])).toBe(false);
	});

	it('matches single person', () => {
		const checkin = createCheckin({ watched_with: 'Family' });
		expect(filterByPeople(checkin, ['Family'])).toBe(true);
		expect(filterByPeople(checkin, ['Friends'])).toBe(false);
	});

	it('matches multiple people options', () => {
		const checkin = createCheckin({ watched_with: 'Alone' });
		expect(filterByPeople(checkin, ['Family', 'Alone', 'Friends'])).toBe(true);
		expect(filterByPeople(checkin, ['Family', 'Friends'])).toBe(false);
	});
});

describe('filterByMediaTypes', () => {
	it('returns true when mediaTypes array is empty', () => {
		const checkin = createCheckin({ content: { name: 'Test', content_type: 'series' } });
		expect(filterByMediaTypes(checkin, [])).toBe(true);
	});

	it('returns false when checkin has no content_type', () => {
		const checkin = createCheckin({ content: { name: 'Test' } });
		expect(filterByMediaTypes(checkin, ['Film'])).toBe(false);
	});

	it('matches Film (movie)', () => {
		const checkin = createCheckin({ content: { name: 'Inception', content_type: 'movie' } });
		expect(filterByMediaTypes(checkin, ['Film'])).toBe(true);
		expect(filterByMediaTypes(checkin, ['TV Series'])).toBe(false);
	});

	it('matches TV Series (series)', () => {
		const checkin = createCheckin({ content: { name: 'Breaking Bad', content_type: 'series' } });
		expect(filterByMediaTypes(checkin, ['TV Series'])).toBe(true);
		expect(filterByMediaTypes(checkin, ['Film'])).toBe(false);
	});

	it('matches multiple media types', () => {
		const seriesCheckin = createCheckin({ content: { name: 'Test', content_type: 'series' } });
		const movieCheckin = createCheckin({ content: { name: 'Test', content_type: 'movie' } });

		expect(filterByMediaTypes(seriesCheckin, ['Film', 'TV Series'])).toBe(true);
		expect(filterByMediaTypes(movieCheckin, ['Film', 'TV Series'])).toBe(true);
	});
});

describe('applyFilters', () => {
	it('returns true when no filters are applied', () => {
		const checkin = createCheckin();
		expect(applyFilters(checkin, {})).toBe(true);
	});

	it('applies all filters together', () => {
		const checkin = createCheckin({
			watched_at: '2024-01-15T20:00:00Z',
			location: 'Home',
			watched_with: 'Family',
			content: { name: 'Breaking Bad', content_type: 'series' }
		});

		const options: FilterOptions = {
			searchQuery: 'breaking',
			startDate: '2024-01-01',
			endDate: '2024-01-31',
			locations: ['Home'],
			people: ['Family'],
			mediaTypes: ['TV Series']
		};

		expect(applyFilters(checkin, options)).toBe(true);
	});

	it('returns false if any filter fails', () => {
		const checkin = createCheckin({
			location: 'Home',
			content: { name: 'Breaking Bad', content_type: 'series' }
		});

		// Wrong location
		expect(
			applyFilters(checkin, { locations: ['Cinema'] })
		).toBe(false);

		// Wrong media type
		expect(
			applyFilters(checkin, { mediaTypes: ['Film'] })
		).toBe(false);

		// Search doesn't match
		expect(
			applyFilters(checkin, { searchQuery: 'nonexistent' })
		).toBe(false);
	});
});

describe('filterCheckins', () => {
	it('filters an array of checkins', () => {
		const checkins: Checkin[] = [
			createCheckin({ id: 1, content: { name: 'Movie A', content_type: 'movie' } }),
			createCheckin({ id: 2, content: { name: 'Series B', content_type: 'series' } }),
			createCheckin({ id: 3, content: { name: 'Movie C', content_type: 'movie' } })
		];

		const result = filterCheckins(checkins, { mediaTypes: ['Film'] });
		expect(result).toHaveLength(2);
		expect(result.map((c) => c.id)).toEqual([1, 3]);
	});

	it('returns empty array when no matches', () => {
		const checkins: Checkin[] = [
			createCheckin({ id: 1, content: { name: 'Test', content_type: 'series' } })
		];

		const result = filterCheckins(checkins, { mediaTypes: ['Film'] });
		expect(result).toHaveLength(0);
	});

	it('returns all checkins when no filters applied', () => {
		const checkins: Checkin[] = [
			createCheckin({ id: 1 }),
			createCheckin({ id: 2 }),
			createCheckin({ id: 3 })
		];

		const result = filterCheckins(checkins, {});
		expect(result).toHaveLength(3);
	});
});

describe('extractUniqueLocations', () => {
	it('extracts unique locations sorted alphabetically', () => {
		const checkins: Checkin[] = [
			createCheckin({ location: 'Cinema' }),
			createCheckin({ location: 'Home' }),
			createCheckin({ location: 'Cinema' }),
			createCheckin({ location: 'Work' }),
			createCheckin({ location: null })
		];

		const result = extractUniqueLocations(checkins);
		expect(result).toEqual(['Cinema', 'Home', 'Work']);
	});

	it('returns empty array when no locations', () => {
		const checkins: Checkin[] = [
			createCheckin({ location: null }),
			createCheckin({ location: undefined })
		];

		const result = extractUniqueLocations(checkins);
		expect(result).toEqual([]);
	});
});

describe('extractUniquePeople', () => {
	it('extracts unique people sorted alphabetically', () => {
		const checkins: Checkin[] = [
			createCheckin({ watched_with: 'Family' }),
			createCheckin({ watched_with: 'Alone' }),
			createCheckin({ watched_with: 'Family' }),
			createCheckin({ watched_with: 'Friends' }),
			createCheckin({ watched_with: null })
		];

		const result = extractUniquePeople(checkins);
		expect(result).toEqual(['Alone', 'Family', 'Friends']);
	});
});

describe('extractUniqueMediaTypes', () => {
	it('extracts unique media types as display labels', () => {
		const checkins: Checkin[] = [
			createCheckin({ content: { name: 'A', content_type: 'movie' } }),
			createCheckin({ content: { name: 'B', content_type: 'series' } }),
			createCheckin({ content: { name: 'C', content_type: 'movie' } }),
			createCheckin({ content: null })
		];

		const result = extractUniqueMediaTypes(checkins);
		expect(result).toEqual(['Film', 'TV Series']);
	});

	it('returns empty array when no content types', () => {
		const checkins: Checkin[] = [
			createCheckin({ content: null }),
			createCheckin({ content: { name: 'Test' } })
		];

		const result = extractUniqueMediaTypes(checkins);
		expect(result).toEqual([]);
	});
});

describe('groupByDay', () => {
	it('groups checkins by day', () => {
		const checkins: Checkin[] = [
			createCheckin({ id: 1, watched_at: '2024-01-15T10:00:00Z' }),
			createCheckin({ id: 2, watched_at: '2024-01-15T20:00:00Z' }),
			createCheckin({ id: 3, watched_at: '2024-01-16T15:00:00Z' })
		];

		const result = groupByDay(checkins);
		expect(result.size).toBe(2);

		const jan15 = result.get('January 15, 2024');
		const jan16 = result.get('January 16, 2024');

		expect(jan15).toHaveLength(2);
		expect(jan16).toHaveLength(1);
	});

	it('returns empty map for empty array', () => {
		const result = groupByDay([]);
		expect(result.size).toBe(0);
	});
});

describe('hasActiveFilters', () => {
	it('returns false when no filters are active', () => {
		expect(hasActiveFilters({})).toBe(false);
		expect(hasActiveFilters({ locations: [], people: [], mediaTypes: [] })).toBe(false);
	});

	it('returns true when searchQuery is set', () => {
		expect(hasActiveFilters({ searchQuery: 'test' })).toBe(true);
	});

	it('returns true when startDate is set', () => {
		expect(hasActiveFilters({ startDate: '2024-01-01' })).toBe(true);
	});

	it('returns true when endDate is set', () => {
		expect(hasActiveFilters({ endDate: '2024-01-31' })).toBe(true);
	});

	it('returns true when locations are selected', () => {
		expect(hasActiveFilters({ locations: ['Home'] })).toBe(true);
	});

	it('returns true when people are selected', () => {
		expect(hasActiveFilters({ people: ['Family'] })).toBe(true);
	});

	it('returns true when mediaTypes are selected', () => {
		expect(hasActiveFilters({ mediaTypes: ['Film'] })).toBe(true);
	});
});
