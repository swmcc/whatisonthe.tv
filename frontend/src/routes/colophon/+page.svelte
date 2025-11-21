<script lang="ts">
	// Static colophon page
</script>

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
	<div class="bg-white shadow rounded-lg p-8">
		<h1 class="text-3xl font-bold text-gray-900 mb-6">Colophon</h1>

		<div class="prose prose-indigo max-w-none">
			<p class="text-lg text-gray-700 mb-6">
				This page details the technology stack and infrastructure powering What Is On The TV.
			</p>

			<h2 class="text-2xl font-semibold text-gray-900 mt-8 mb-4">Backend</h2>
			<ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
				<li><strong>Framework:</strong> <a href="https://fastapi.tiangolo.com/" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">FastAPI</a> - Modern Python web framework for building APIs</li>
				<li><strong>Database:</strong> <a href="https://www.postgresql.org/" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">PostgreSQL 16</a> - Robust relational database</li>
				<li><strong>Cache:</strong> <a href="https://redis.io/" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">Redis 7</a> - In-memory data structure store</li>
				<li><strong>Task Queue:</strong> <a href="https://docs.celeryq.dev/" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">Celery</a> - Distributed task queue for background processing</li>
				<li><strong>ORM:</strong> <a href="https://www.sqlalchemy.org/" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">SQLAlchemy</a> - Python SQL toolkit</li>
				<li><strong>Python:</strong> Version 3.12+</li>
			</ul>

			<h2 class="text-2xl font-semibold text-gray-900 mt-8 mb-4">Frontend</h2>
			<ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
				<li><strong>Framework:</strong> <a href="https://kit.svelte.dev/" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">SvelteKit 2.x</a> - The fastest way to build Svelte apps</li>
				<li><strong>UI Framework:</strong> <a href="https://svelte.dev/" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">Svelte 4.x</a> - Cybernetically enhanced web apps</li>
				<li><strong>Build Tool:</strong> <a href="https://vitejs.dev/" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">Vite 5.x</a> - Next generation frontend tooling</li>
				<li><strong>Language:</strong> <a href="https://www.typescriptlang.org/" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">TypeScript</a> - Typed superset of JavaScript</li>
				<li><strong>Styling:</strong> <a href="https://tailwindcss.com/" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">Tailwind CSS</a> - Utility-first CSS framework</li>
			</ul>

			<h2 class="text-2xl font-semibold text-gray-900 mt-8 mb-4">External Services</h2>
			<ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
				<li><strong>TV & Movie Data:</strong> <a href="https://thetvdb.com/" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">TheTVDB API v4</a> - Comprehensive entertainment database</li>
			</ul>

			<h2 class="text-2xl font-semibold text-gray-900 mt-8 mb-4">Infrastructure</h2>
			<p class="text-gray-700 mb-4">
				Currently hosted on <a href="https://www.heroku.com/" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">Heroku</a> as a convenience for rapid deployment. The application runs across multiple dynos:
			</p>
			<ul class="list-disc list-inside space-y-2 text-gray-700 mb-4">
				<li><strong>Web:</strong> FastAPI application serving both API and static frontend</li>
				<li><strong>Worker:</strong> Celery workers handling background tasks</li>
				<li><strong>Redis:</strong> Heroku Redis for caching and Celery broker</li>
				<li><strong>Database:</strong> Heroku Postgres</li>
			</ul>
			<p class="text-gray-700 mb-6">
				The plan is to migrate to a more cost-effective self-hosted solution in the future.
			</p>

			<h2 class="text-2xl font-semibold text-gray-900 mt-8 mb-4">Development</h2>
			<ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
				<li><strong>Code Quality:</strong> ruff, mypy, black for Python; ESLint for TypeScript</li>
				<li><strong>Testing:</strong> pytest for backend tests</li>
				<li><strong>Version Control:</strong> Git</li>
				<li><strong>Task Runner:</strong> Make - all common tasks via Makefile</li>
			</ul>

			<h2 class="text-2xl font-semibold text-gray-900 mt-8 mb-4">More Information</h2>
			<p class="text-gray-700 mb-4">
				Read more about this project in the <a href="https://swm.cc/projects/building-whatisonthetv/" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">blog post</a> explaining the motivation and technical decisions.
			</p>
			<p class="text-gray-700 mb-6">
				The complete source code is available on <a href="https://github.com/swmcc/whatisonthe.tv" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">GitHub</a>.
			</p>

			<h2 class="text-2xl font-semibold text-gray-900 mt-8 mb-4">Built With ❤️</h2>
			<p class="text-gray-700 mb-4">
				This application was crafted with <a href="https://neovim.io" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">Neovim</a> in conjunction with <a href="https://claude.ai" class="text-indigo-600 hover:text-indigo-500" target="_blank" rel="noopener noreferrer">Claude AI</a>.
			</p>
			<p class="text-gray-700">
				Developed on a 2024 14" MacBook Pro with M4 chip.
			</p>
		</div>
	</div>
</div>
