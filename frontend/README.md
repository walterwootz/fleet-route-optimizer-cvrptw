# RailFleet Manager - Frontend

Modern React + TypeScript frontend for RailFleet Manager with FLEET-ONE AI Agent integration.

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **UI Components**: Tremor (Dashboard & Analytics)
- **Icons**: Lucide React
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Routing**: React Router (coming soon)

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── FleetOne/          # FLEET-ONE Chat components
│   │       ├── FleetOneContainer.tsx
│   │       ├── FleetOneTrigger.tsx
│   │       ├── FleetOneDrawer.tsx (TODO)
│   │       ├── ChatHeader.tsx (TODO)
│   │       ├── MessageList.tsx (TODO)
│   │       ├── ChatInput.tsx (TODO)
│   │       └── ModeIndicator.tsx (TODO)
│   ├── pages/
│   │   └── Dashboard.tsx      # Main dashboard with KPIs
│   ├── stores/
│   │   └── fleetOneStore.ts   # Zustand store for FLEET-ONE
│   ├── services/
│   │   └── fleetOneApi.ts     # API client for backend
│   ├── types/
│   │   └── fleetOne.ts        # TypeScript types
│   ├── lib/                   # Utility functions (TODO)
│   ├── App.tsx                # Main application
│   ├── main.tsx               # Entry point
│   └── index.css              # Global styles
├── public/                    # Static assets
├── tailwind.config.js         # Tailwind configuration
├── vite.config.ts             # Vite configuration (with API proxy)
└── package.json
```

## Setup & Development

### Install Dependencies

```bash
npm install
```

### Start Development Server

```bash
npm run dev
```

Frontend runs on **http://localhost:3000**

The Vite proxy forwards `/api/*` requests to the backend at `http://localhost:8000`.

### Start Backend (Required)

In the root directory:

```bash
uvicorn src.app:app --reload --port 8000
```

### Build for Production

```bash
npm run build
```

Output: `dist/` folder

### Preview Production Build

```bash
npm run preview
```

## Features

### ✅ Implemented (Phase 1 - MVP Setup)

- [x] Vite + React + TypeScript setup
- [x] TailwindCSS configuration
- [x] Tremor dashboard components
- [x] Basic folder structure
- [x] FLEET-ONE API client (`fleetOneApi.ts`)
- [x] Zustand store for state management
- [x] TypeScript types for FLEET-ONE
- [x] Dashboard page with mock KPIs
- [x] FLEET-ONE trigger button (floating)
- [x] Basic App layout (header + footer)

### 🚧 In Progress (Phase 2 - FLEET-ONE Chat)

- [ ] FleetOneDrawer component
- [ ] ChatHeader with session info
- [ ] MessageList with auto-scroll
- [ ] UserMessage / AssistantMessage components
- [ ] ChatInput with mode picker
- [ ] ModeIndicator (7 modes with colors)
- [ ] StructuredDataRenderer (tables, charts)
- [ ] Error handling & loading states

### 📋 TODO (Phase 3 - Full Dashboard)

- [ ] Fleet overview page (table with filters)
- [ ] Maintenance calendar view
- [ ] Workshop management page
- [ ] Reports & analytics
- [ ] Document management
- [ ] React Router navigation
- [ ] Authentication & RBAC
- [ ] Responsive mobile layout

## FLEET-ONE Integration

### API Endpoints

All requests proxy through Vite to `http://localhost:8000/api/v1`:

- `POST /fleet-one/session` - Create session
- `POST /fleet-one/query` - Send query
- `GET /fleet-one/session/{id}/history` - Get history
- `DELETE /fleet-one/session/{id}` - Clear session
- `GET /fleet-one/modes` - List modes
- `GET /fleet-one/metrics` - Agent metrics
- `GET /fleet-one/health` - Health check

### Usage Example

```tsx
import { useFleetOneStore } from '@/stores/fleetOneStore';

function MyComponent() {
  const { sendQuery, messages, loading } = useFleetOneStore();

  const handleQuery = () => {
    sendQuery('Zeige mir alle Loks mit Status maintenance_due');
  };

  return (
    <div>
      {messages.map((msg, idx) => (
        <div key={idx}>{msg.content}</div>
      ))}
      <button onClick={handleQuery} disabled={loading}>
        Query senden
      </button>
    </div>
  );
}
```

## Styling Guidelines

### Tremor Components

Use Tremor for dashboard widgets:

```tsx
import { Card, Title, Metric, BarChart } from '@tremor/react';

<Card>
  <Title>Verfügbarkeit</Title>
  <Metric>92.5%</Metric>
  <BarChart data={data} {...props} />
</Card>
```

### TailwindCSS Classes

Follow utility-first approach:

```tsx
<div className="flex items-center space-x-4 p-6 bg-white rounded-lg shadow">
  {/* content */}
</div>
```

### Custom Colors

FLEET-ONE brand colors defined in `tailwind.config.js`:

- `bg-fleet-blue-600` - Primary blue
- `text-fleet-blue-700` - Dark blue

## Development Guidelines

### Component Structure

```tsx
/**
 * Component Description
 * Purpose and responsibility
 */

import { /* imports */ } from 'library';

interface ComponentProps {
  // props
}

export function Component({ prop }: ComponentProps) {
  // logic

  return (
    // JSX
  );
}
```

### TypeScript

- Use explicit types for props
- Define interfaces in `src/types/`
- Use `type` for unions, `interface` for objects

### State Management

- Use Zustand for global state (FLEET-ONE)
- Use local state (`useState`) for component-specific state
- Keep stores focused and modular

## Environment Variables

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

Access in code:

```ts
const apiUrl = import.meta.env.VITE_API_URL;
```

## Testing (TODO)

```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e
```

## Troubleshooting

### Backend connection fails

1. Ensure backend is running: `uvicorn src.app:app --reload --port 8000`
2. Check proxy config in `vite.config.ts`
3. Verify CORS settings in backend

### Tremor components not styled

1. Check Tailwind content paths include `node_modules/@tremor/**`
2. Rebuild: `npm run dev` (restart dev server)

### TypeScript errors

```bash
npm run tsc
```

## Links

- [Vite Docs](https://vitejs.dev/)
- [React Docs](https://react.dev/)
- [Tremor Docs](https://tremor.so/docs)
- [TailwindCSS Docs](https://tailwindcss.com/)
- [Zustand Docs](https://zustand-demo.pmnd.rs/)

---

**Version**: 1.0.0 (MVP)
**Last Updated**: November 2025
