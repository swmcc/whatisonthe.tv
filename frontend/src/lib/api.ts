import { auth, isTokenExpired } from './stores/auth';
import { get } from 'svelte/store';
import { goto } from '$app/navigation';
import { browser } from '$app/environment';

// Use relative URLs in production (empty string), localhost in development
const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.MODE === 'production' ? '' : 'http://localhost:8000');

interface RequestOptions extends RequestInit {
	requiresAuth?: boolean;
}

/**
 * Custom error class for authentication failures.
 * Allows callers to distinguish auth errors from other errors.
 */
export class AuthenticationError extends Error {
	constructor(message: string = 'Your session has expired. Please log in again.') {
		super(message);
		this.name = 'AuthenticationError';
	}
}

async function request(endpoint: string, options: RequestOptions = {}) {
	const { requiresAuth = false, ...fetchOptions } = options;

	const headers: Record<string, string> = {
		'Content-Type': 'application/json'
	};

	// Merge any additional headers from options
	if (fetchOptions.headers) {
		const additionalHeaders = fetchOptions.headers as Record<string, string>;
		Object.assign(headers, additionalHeaders);
	}

	if (requiresAuth) {
		// Read token directly from localStorage as primary source
		let token: string | null = null;
		if (browser) {
			token = localStorage.getItem('token');
		}

		// Fallback to store if localStorage didn't work
		if (!token) {
			const authState = get(auth);
			token = authState.token;
		}

		console.log('[API] requiresAuth request to:', endpoint);
		console.log('[API] token exists:', !!token);

		// Check if token is expired before making the request
		if (!token || isTokenExpired(token)) {
			console.log('[API] Token missing or expired');
			auth.handleAuthError();
			if (browser) {
				goto('/login');
			}
			throw new AuthenticationError();
		}

		headers['Authorization'] = `Bearer ${token}`;
		console.log('[API] Authorization header set');
	}

	const url = `${API_URL}${endpoint}`;
	console.log('[API] Fetching:', url);
	console.log('[API] Headers:', JSON.stringify(headers));

	const response = await fetch(url, {
		...fetchOptions,
		headers
	});

	console.log('[API] Response status:', response.status);

	// Handle 401 Unauthorized globally
	if (response.status === 401) {
		auth.handleAuthError();
		if (browser) {
			goto('/login');
		}
		throw new AuthenticationError();
	}

	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
		throw new Error(error.detail || `HTTP error ${response.status}`);
	}

	// Handle 204 No Content responses
	if (response.status === 204) {
		return null;
	}

	return response.json();
}

export const api = {
	auth: {
		login: async (email: string, password: string) => {
			return request('/api/auth/login', {
				method: 'POST',
				body: JSON.stringify({ email, password })
			});
		},
		logout: async () => {
			return request('/api/auth/logout', {
				method: 'POST',
				requiresAuth: true
			});
		},
		me: async () => {
			return request('/api/auth/me', {
				requiresAuth: true
			});
		},
		getPublicUser: async (username: string) => {
			return request(`/api/auth/user/${username}`, {
				requiresAuth: false
			});
		},
		updateProfile: async (data: { username?: string | null; first_name?: string; last_name?: string }) => {
			return request('/api/auth/me', {
				method: 'PATCH',
				body: JSON.stringify(data),
				requiresAuth: true
			});
		},
		updatePassword: async (current_password: string, new_password: string) => {
			return request('/api/auth/me/password', {
				method: 'POST',
				body: JSON.stringify({ current_password, new_password }),
				requiresAuth: true
			});
		}
	},
	search: {
		query: async (q: string, limit: number = 20, offset: number = 0) => {
			return request(`/api/search?q=${encodeURIComponent(q)}&limit=${limit}&offset=${offset}`, {
				requiresAuth: true
			});
		},
		getSeries: async (id: number) => {
			return request(`/api/series/${id}`, {
				requiresAuth: true
			});
		},
		getMovie: async (id: number) => {
			return request(`/api/movie/${id}`, {
				requiresAuth: true
			});
		},
		getPerson: async (id: number) => {
			return request(`/api/person/${id}`, {
				requiresAuth: true
			});
		},
		getSeriesSeasons: async (id: number) => {
			return request(`/api/series/${id}/seasons`, {
				requiresAuth: true
			});
		},
		getSeriesEpisodes: async (id: number) => {
			return request(`/api/series/${id}/episodes`, {
				requiresAuth: true
			});
		},
		getSeasonEpisodes: async (id: number, seasonNumber: number) => {
			return request(`/api/series/${id}/season/${seasonNumber}/episodes`, {
				requiresAuth: true
			});
		}
	},
	checkin: {
		create: async (data: {
			content_id: number;
			episode_id?: number;
			watched_at: string;
			location?: string;
			watched_with?: string;
			notes?: string;
			focus?: 'focused' | 'distracted' | 'background' | 'sleep';
		}) => {
			return request('/api/checkins', {
				method: 'POST',
				body: JSON.stringify(data),
				requiresAuth: true
			});
		},
		list: async (days: number = 10, beforeDate?: string) => {
			const params = new URLSearchParams({ days: days.toString() });
			if (beforeDate) {
				params.append('before_date', beforeDate);
			}
			return request(`/api/checkins?${params.toString()}`, {
				requiresAuth: true
			});
		},
		listByUsername: async (username: string, days: number = 10, beforeDate?: string) => {
			const params = new URLSearchParams({ days: days.toString() });
			if (beforeDate) {
				params.append('before_date', beforeDate);
			}
			return request(`/api/checkins/user/${username}?${params.toString()}`, {
				requiresAuth: false
			});
		},
		get: async (id: number) => {
			return request(`/api/checkins/${id}`, {
				requiresAuth: true
			});
		},
		update: async (
			id: number,
			data: {
				watched_at?: string;
				location?: string;
				watched_with?: string;
				notes?: string;
				focus?: 'focused' | 'distracted' | 'background' | 'sleep' | null;
			}
		) => {
			return request(`/api/checkins/${id}`, {
				method: 'PATCH',
				body: JSON.stringify(data),
				requiresAuth: true
			});
		},
		delete: async (id: number) => {
			return request(`/api/checkins/${id}`, {
				method: 'DELETE',
				requiresAuth: true
			});
		},
		listByContent: async (contentId: number) => {
			return request(`/api/checkins/content/${contentId}`, {
				requiresAuth: true
			});
		}
	},
	watchlist: {
		list: async (itemType?: 'content' | 'person') => {
			const params = new URLSearchParams();
			if (itemType) {
				params.append('item_type', itemType);
			}
			const queryString = params.toString();
			return request(`/api/watchlist${queryString ? `?${queryString}` : ''}`, {
				requiresAuth: true
			});
		},
		addContent: async (tvdbId: number, notes?: string) => {
			return request('/api/watchlist/content', {
				method: 'POST',
				body: JSON.stringify({ tvdb_id: tvdbId, notes }),
				requiresAuth: true
			});
		},
		addPerson: async (
			personId: number,
			personRoleFilter: 'any' | 'actor' | 'director' = 'any',
			notes?: string
		) => {
			return request('/api/watchlist/person', {
				method: 'POST',
				body: JSON.stringify({
					person_id: personId,
					person_role_filter: personRoleFilter,
					notes
				}),
				requiresAuth: true
			});
		},
		updateContent: async (tvdbId: number, notes?: string) => {
			return request(`/api/watchlist/content/${tvdbId}`, {
				method: 'PATCH',
				body: JSON.stringify({ notes }),
				requiresAuth: true
			});
		},
		updatePerson: async (
			personId: number,
			personRoleFilter?: 'any' | 'actor' | 'director',
			notes?: string
		) => {
			return request(`/api/watchlist/person/${personId}`, {
				method: 'PATCH',
				body: JSON.stringify({ person_role_filter: personRoleFilter, notes }),
				requiresAuth: true
			});
		},
		removeContent: async (tvdbId: number) => {
			return request(`/api/watchlist/content/${tvdbId}`, {
				method: 'DELETE',
				requiresAuth: true
			});
		},
		removePerson: async (personId: number) => {
			return request(`/api/watchlist/person/${personId}`, {
				method: 'DELETE',
				requiresAuth: true
			});
		},
		checkContent: async (tvdbId: number) => {
			return request(`/api/watchlist/check/content/${tvdbId}`, {
				requiresAuth: true
			});
		},
		checkPerson: async (personId: number) => {
			return request(`/api/watchlist/check/person/${personId}`, {
				requiresAuth: true
			});
		},
		// Updates
		getUpdates: async (unreadOnly: boolean = false, limit: number = 50) => {
			const params = new URLSearchParams();
			if (unreadOnly) params.append('unread_only', 'true');
			if (limit !== 50) params.append('limit', limit.toString());
			const queryString = params.toString();
			return request(`/api/watchlist/updates${queryString ? `?${queryString}` : ''}`, {
				requiresAuth: true
			});
		},
		getUpdatesCount: async () => {
			return request('/api/watchlist/updates/count', {
				requiresAuth: true
			});
		},
		markUpdateRead: async (updateId: number) => {
			return request(`/api/watchlist/updates/${updateId}/read`, {
				method: 'POST',
				requiresAuth: true
			});
		},
		markAllUpdatesRead: async () => {
			return request('/api/watchlist/updates/read-all', {
				method: 'POST',
				requiresAuth: true
			});
		}
	},
	swanson: {
		recommend: async (data: {
			prompt: string;
			search_results: Array<{
				id: number;
				name: string;
				type: string;
				year?: number;
				genres?: string[];
			}>;
			feedback?: Array<{
				name: string;
				type: string;
				rating: 'dislike' | 'like' | 'love';
			}>;
			previous_recommendations?: string[];
		}) => {
			return request('/api/swanson/recommend', {
				method: 'POST',
				body: JSON.stringify(data),
				requiresAuth: true
			});
		},
		// Streaming version - returns an async iterator of text chunks
		stream: async function* (data: {
			prompt: string;
			search_results: Array<{
				id: number;
				name: string;
				type: string;
				year?: number;
				genres?: string[];
			}>;
			feedback?: Array<{
				name: string;
				type: string;
				rating: 'dislike' | 'like' | 'love';
			}>;
			previous_recommendations?: string[];
		}): AsyncGenerator<string, void, unknown> {
			console.log('[API] stream() called with prompt:', data.prompt.substring(0, 50));
			const authState = get(auth);

			if (!authState.token || isTokenExpired(authState.token)) {
				console.log('[API] Token expired or missing');
				auth.handleAuthError();
				if (browser) {
					goto('/login');
				}
				throw new AuthenticationError();
			}

			console.log('[API] Fetching stream from:', `${API_URL}/api/swanson/recommend/stream`);
			const response = await fetch(`${API_URL}/api/swanson/recommend/stream`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${authState.token}`
				},
				body: JSON.stringify(data)
			});

			console.log('[API] Response status:', response.status);
			if (!response.ok) {
				const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
				console.log('[API] Error response:', error);
				throw new Error(error.detail || `HTTP error ${response.status}`);
			}

			const reader = response.body?.getReader();
			if (!reader) throw new Error('No response body');

			const decoder = new TextDecoder();
			let buffer = '';

			while (true) {
				const { done, value } = await reader.read();
				if (done) {
					console.log('[API] Stream done, remaining buffer:', buffer);
					break;
				}

				buffer += decoder.decode(value, { stream: true });

				// Parse SSE format: "data: <content>\n\n"
				const lines = buffer.split('\n\n');
				buffer = lines.pop() || ''; // Keep incomplete line in buffer

				for (const line of lines) {
					if (line.startsWith('data: ')) {
						const content = line.slice(6);
						if (content === '[DONE]') {
							console.log('[API] Received [DONE]');
							return;
						}
						if (content.startsWith('[ERROR]')) {
							console.log('[API] Received error:', content);
							throw new Error(content.slice(8));
						}
						// Parse JSON to handle newlines properly
						try {
							yield JSON.parse(content);
						} catch {
							yield content;
						}
					}
				}
			}
		}
	}
};
