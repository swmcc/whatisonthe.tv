# WatchLog Frontend

SvelteKit frontend for WatchLog.

## Setup

To initialize the SvelteKit project, run:

```bash
cd frontend
npm create svelte@latest .

# When prompted:
# - Choose "Skeleton project"
# - TypeScript: Yes
# - ESLint: Yes
# - Prettier: Yes
# - Playwright: No (optional)
# - Vitest: No (optional)

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:5173

## Development

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run check

# Linting
npm run lint
```

## API Integration

The backend API runs at http://localhost:8000

Configure the API base URL in your environment or config.
