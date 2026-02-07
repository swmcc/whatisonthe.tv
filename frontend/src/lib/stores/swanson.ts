import { writable } from 'svelte/store';

interface Message {
	role: 'user' | 'swanson';
	content: string;
}

// Global stores for Swanson chat state
export const swansonLoading = writable(false);
export const swansonStreamingText = writable('');
export const swansonMessages = writable<Message[]>([]);

// Reset stores when starting a new session
export function resetSwansonStores() {
	swansonLoading.set(false);
	swansonStreamingText.set('');
	// Don't reset messages - we want them to persist
}
