import { writable, get } from 'svelte/store';
import { browser } from '$app/environment';

export interface User {
	id: number;
	email: string;
	username: string | null;
	first_name: string;
	last_name: string;
	created_at: string;
	updated_at: string;
}

interface AuthState {
	user: User | null;
	token: string | null;
	loading: boolean;
}

/**
 * Decode a JWT token and return the payload.
 * Returns null if the token is invalid or malformed.
 */
function decodeJwt(token: string): { exp?: number; [key: string]: unknown } | null {
	try {
		const parts = token.split('.');
		if (parts.length !== 3) return null;
		const payload = parts[1];
		const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
		return JSON.parse(decoded);
	} catch {
		return null;
	}
}

/**
 * Check if a JWT token is expired.
 * Returns true if expired or invalid, false if still valid.
 */
function isTokenExpired(token: string | null): boolean {
	if (!token) return true;
	const payload = decodeJwt(token);
	if (!payload || !payload.exp) return true;
	// Add 30 second buffer to avoid edge cases
	return Date.now() >= (payload.exp * 1000) - 30000;
}

/**
 * Get a valid token from localStorage, or null if expired/missing.
 */
function getValidToken(): string | null {
	if (!browser) return null;
	const token = localStorage.getItem('token');
	if (isTokenExpired(token)) {
		// Clean up expired token
		localStorage.removeItem('token');
		localStorage.removeItem('user');
		return null;
	}
	return token;
}

/**
 * Get user from localStorage only if token is valid.
 */
function getValidUser(): User | null {
	if (!browser) return null;
	const token = getValidToken();
	if (!token) return null;
	try {
		return JSON.parse(localStorage.getItem('user') || 'null');
	} catch {
		return null;
	}
}

const initialState: AuthState = {
	user: getValidUser(),
	token: getValidToken(),
	loading: false
};

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>(initialState);

	const logout = () => {
		if (browser) {
			localStorage.removeItem('token');
			localStorage.removeItem('user');
		}
		set({ user: null, token: null, loading: false });
	};

	return {
		subscribe,
		login: (user: User, token: string) => {
			if (browser) {
				localStorage.setItem('token', token);
				localStorage.setItem('user', JSON.stringify(user));
			}
			set({ user, token, loading: false });
		},
		logout,
		setUser: (user: User) => {
			if (browser) {
				localStorage.setItem('user', JSON.stringify(user));
			}
			update(state => ({ ...state, user }));
		},
		setLoading: (loading: boolean) => {
			update(state => ({ ...state, loading }));
		},
		/**
		 * Check if the current token is valid (exists and not expired).
		 * If expired, automatically clears auth state.
		 */
		isValid: (): boolean => {
			const state = get({ subscribe });
			if (!state.token) return false;
			if (isTokenExpired(state.token)) {
				logout();
				return false;
			}
			return true;
		},
		/**
		 * Clear auth state due to an authentication error (e.g., 401 response).
		 */
		handleAuthError: () => {
			logout();
		}
	};
}

export const auth = createAuthStore();
export { isTokenExpired };
