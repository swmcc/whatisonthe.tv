import { writable, get } from 'svelte/store';

export type Rating = 'dislike' | 'like' | 'love';

export interface SearchResult {
	id: number;
	name: string;
	type: string;
	year?: number;
	image?: string;
	rating?: Rating;
}

export interface FeedbackItem {
	name: string;
	type: string;
	rating: Rating;
}

export interface Message {
	role: 'user' | 'swanson';
	content: string;
	recommendations?: SearchResult[];
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

// Parse titles from TITLES: line in response
export function parseTitles(content: string): { cleanContent: string; titles: string[] } {
	const titlesMatch = content.match(/\nTITLES:\s*(.+)$/i);
	if (titlesMatch) {
		const titles = titlesMatch[1].split(',').map(t => t.trim()).filter(t => t.length > 0);
		const cleanContent = content.replace(/\nTITLES:\s*.+$/i, '').trim();
		return { cleanContent, titles };
	}
	return { cleanContent: content, titles: [] };
}

// Collect all feedback from messages
export function collectFeedback(): FeedbackItem[] {
	const messages = get(swansonMessages);
	const feedback: FeedbackItem[] = [];

	for (const msg of messages) {
		if (msg.role === 'swanson' && msg.recommendations) {
			for (const rec of msg.recommendations) {
				if (rec.rating) {
					feedback.push({
						name: rec.name,
						type: rec.type,
						rating: rec.rating
					});
				}
			}
		}
	}

	return feedback;
}

// Collect all previously recommended titles
export function collectPreviousRecommendations(): string[] {
	const messages = get(swansonMessages);
	const titles: string[] = [];

	for (const msg of messages) {
		if (msg.role === 'swanson' && msg.recommendations) {
			for (const rec of msg.recommendations) {
				titles.push(rec.name);
			}
		}
	}

	return titles;
}
