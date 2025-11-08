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
	user: null,
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
			}
			set({ user, token, loading: false });
		},
		logout: () => {
			if (browser) {
				localStorage.removeItem('token');
			}
			set({ user: null, token: null, loading: false });
		},
		setUser: (user: User) => {
			update(state => ({ ...state, user }));
		},
		setLoading: (loading: boolean) => {
			update(state => ({ ...state, loading }));
		}
	};
}

export const auth = createAuthStore();
