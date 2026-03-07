import { writable, get } from 'svelte/store';
import { api } from '$lib/api';
import { auth } from '$lib/stores/auth';
import { browser } from '$app/environment';

export interface Update {
	id: number;
	description: string;
	update_type: string;
	is_read: boolean;
	created_at: string;
	watchlist_item?: {
		id: number;
		item_type: string;
		content?: {
			id: number;
			tvdb_id: number;
			name: string;
			image_url?: string;
			poster_url?: string;
		};
		person?: {
			id: number;
			tvdb_id: number;
			full_name: string;
			image_url?: string;
		};
	};
}

// Create the writable store
const store = writable<Update[]>([]);
let pollInterval: ReturnType<typeof setInterval> | null = null;
let isLoading = false;

// Load updates from API
async function load(unreadOnly: boolean = true, limit: number = 10) {
	if (!browser || !auth.isValid() || isLoading) return;
	isLoading = true;
	try {
		const data = await api.watchlist.getUpdates(unreadOnly, limit);
		store.set(data);
	} catch (e) {
		console.error('Failed to load updates:', e);
	} finally {
		isLoading = false;
	}
}

// Start polling for updates
function startPolling(intervalMs: number = 30000) {
	if (!browser) return;
	stopPolling();
	pollInterval = setInterval(load, intervalMs);
}

// Stop polling
function stopPolling() {
	if (pollInterval) {
		clearInterval(pollInterval);
		pollInterval = null;
	}
}

// Mark single update as read
async function markAsRead(updateId: number) {
	try {
		await api.watchlist.markUpdateRead(updateId);
		store.update(updates => updates.filter(u => u.id !== updateId));
	} catch (e) {
		console.error('Failed to mark update as read:', e);
	}
}

// Mark all as read
async function markAllAsRead() {
	try {
		await api.watchlist.markAllUpdatesRead();
		store.set([]);
	} catch (e) {
		// Ignore errors
	}
}

// Clear store
function clear() {
	store.set([]);
	stopPolling();
}

// Export store with methods
export const updates = {
	subscribe: store.subscribe,
	load,
	startPolling,
	stopPolling,
	markAsRead,
	markAllAsRead,
	clear
};
