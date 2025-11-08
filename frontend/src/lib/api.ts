import { auth } from './stores/auth';
import { get } from 'svelte/store';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface RequestOptions extends RequestInit {
	requiresAuth?: boolean;
}

async function request(endpoint: string, options: RequestOptions = {}) {
	const { requiresAuth = false, ...fetchOptions } = options;

	const headers: HeadersInit = {
		'Content-Type': 'application/json',
		...(fetchOptions.headers || {})
	};

	if (requiresAuth) {
		const authState = get(auth);
		if (authState.token) {
			headers['Authorization'] = `Bearer ${authState.token}`;
		}
	}

	const response = await fetch(`${API_URL}${endpoint}`, {
		...fetchOptions,
		headers
	});

	if (!response.ok) {
		if (response.status === 401) {
			auth.logout();
		}
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
		updateProfile: async (data: { first_name?: string; last_name?: string }) => {
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
		}
	}
};
