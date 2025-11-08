<script lang="ts">
	const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
</script>

<svelte:head>
	<title>What Is On The TV</title>
</svelte:head>

<main>
	<h1>What Is On The TV</h1>
	<p>Watch logging and tracking application</p>
	<p class="api-info">API: {apiUrl}</p>
</main>

<style>
	main {
		padding: 2rem;
		max-width: 800px;
		margin: 0 auto;
		font-family: system-ui, -apple-system, sans-serif;
	}

	h1 {
		color: #333;
		margin-bottom: 1rem;
	}

	.api-info {
		color: #666;
		font-size: 0.9rem;
		margin-top: 2rem;
	}
</style>
