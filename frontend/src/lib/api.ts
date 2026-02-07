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

	const headers: HeadersInit = {
		'Content-Type': 'application/json',
		...(fetchOptions.headers || {})
	};

	if (requiresAuth) {
		const authState = get(auth);

		// Check if token is expired before making the request
		if (!authState.token || isTokenExpired(authState.token)) {
			auth.handleAuthError();
			if (browser) {
				goto('/login');
			}
			throw new AuthenticationError();
		}

		headers['Authorization'] = `Bearer ${authState.token}`;
	}

	const response = await fetch(`${API_URL}${endpoint}`, {
		...fetchOptions,
		headers
	});

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

	return response.json();
}

export const api = {
	auth: {
		login: async (email: string, password: string) => {
			return request('/auth/login', {
				method: 'POST',
				body: JSON.stringify({ email, password })
			});
		},
		logout: async () => {
			return request('/auth/logout', {
				method: 'POST',
				requiresAuth: true
			});
		},
		me: async () => {
			return request('/auth/me', {
				requiresAuth: true
			});
		},
		getPublicUser: async (username: string) => {
			return request(`/auth/user/${username}`, {
				requiresAuth: false
			});
		},
		updateProfile: async (data: { username?: string | null; first_name?: string; last_name?: string }) => {
			return request('/auth/me', {
				method: 'PATCH',
				body: JSON.stringify(data),
				requiresAuth: true
			});
		},
		updatePassword: async (current_password: string, new_password: string) => {
			return request('/auth/me/password', {
				method: 'POST',
				body: JSON.stringify({ current_password, new_password }),
				requiresAuth: true
			});
		}
	},
	search: {
		query: async (q: string, limit: number = 20, offset: number = 0) => {
			return request(`/search?q=${encodeURIComponent(q)}&limit=${limit}&offset=${offset}`, {
				requiresAuth: true
			});
		},
		getSeries: async (id: number) => {
			return request(`/series/${id}`, {
				requiresAuth: true
			});
		},
		getMovie: async (id: number) => {
			return request(`/movie/${id}`, {
				requiresAuth: true
			});
		},
		getPerson: async (id: number) => {
			return request(`/person/${id}`, {
				requiresAuth: true
			});
		},
		getSeriesSeasons: async (id: number) => {
			return request(`/series/${id}/seasons`, {
				requiresAuth: true
			});
		},
		getSeriesEpisodes: async (id: number) => {
			return request(`/series/${id}/episodes`, {
				requiresAuth: true
			});
		},
		getSeasonEpisodes: async (id: number, seasonNumber: number) => {
			return request(`/series/${id}/season/${seasonNumber}/episodes`, {
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
		}) => {
			return request('/checkins', {
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
			return request(`/checkins?${params.toString()}`, {
				requiresAuth: true
			});
		},
		listByUsername: async (username: string, days: number = 10, beforeDate?: string) => {
			const params = new URLSearchParams({ days: days.toString() });
			if (beforeDate) {
				params.append('before_date', beforeDate);
			}
			return request(`/checkins/user/${username}?${params.toString()}`, {
				requiresAuth: false
			});
		},
		get: async (id: number) => {
			return request(`/checkins/${id}`, {
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
			}
		) => {
			return request(`/checkins/${id}`, {
				method: 'PATCH',
				body: JSON.stringify(data),
				requiresAuth: true
			});
		},
		delete: async (id: number) => {
			return request(`/checkins/${id}`, {
				method: 'DELETE',
				requiresAuth: true
			});
		},
		listByContent: async (contentId: number) => {
			return request(`/checkins/content/${contentId}`, {
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
			return request('/swanson/recommend', {
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

			console.log('[API] Fetching stream from:', `${API_URL}/swanson/recommend/stream`);
			const response = await fetch(`${API_URL}/swanson/recommend/stream`, {
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
