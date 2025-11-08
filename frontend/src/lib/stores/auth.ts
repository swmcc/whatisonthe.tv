import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export interface User {
	id: number;
	email: string;
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

const initialState: AuthState = {
	user: browser ? JSON.parse(localStorage.getItem('user') || 'null') : null,
	token: browser ? localStorage.getItem('token') : null,
	loading: false
};

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>(initialState);

	return {
		subscribe,
		login: (user: User, token: string) => {
			if (browser) {
				localStorage.setItem('token', token);
				localStorage.setItem('user', JSON.stringify(user));
			}
			set({ user, token, loading: false });
		},
		logout: () => {
			if (browser) {
				localStorage.removeItem('token');
				localStorage.removeItem('user');
			}
			set({ user: null, token: null, loading: false });
		},
		setUser: (user: User) => {
			if (browser) {
				localStorage.setItem('user', JSON.stringify(user));
			}
			update(state => ({ ...state, user }));
		},
		setLoading: (loading: boolean) => {
			update(state => ({ ...state, loading }));
		}
	};
}

export const auth = createAuthStore();
