# ProbaLab Web — V2 Frontend

Brand-new SPA built in parallel with `ProbaLab/dashboard/` (legacy). Will replace it via DNS switch in P6.

## Stack

Vite 7 · React 19 · TypeScript 5.7 strict · Tailwind CSS 4 · shadcn/ui · Radix · Framer Motion · React Router 7 · TanStack Query 5 · Supabase JS 2

## Quick start

```bash
cd web
cp .env.example .env.local
# Fill in VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL with real values
npm install
npm run dev
```

Open http://localhost:5173.

## Scripts

| Script | What it does |
|---|---|
| `npm run dev` | Vite dev server with HMR |
| `npm run build` | Type-check + production build to `dist/` |
| `npm run preview` | Serve `dist/` locally |
| `npm run lint` | ESLint check |
| `npm run typecheck` | TS check without emit |
| `npm run test:ci` | Vitest unit tests one-shot |
| `npm run e2e` | Playwright E2E (requires `SUPABASE_SERVICE_ROLE_KEY` env var) |

### Running E2E tests locally

```bash
export VITE_SUPABASE_URL="https://yourproject.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="eyJ...service-role..."   # from Supabase Studio → Project Settings → API
cd web && npm run e2e
```

Three tests : signup confirmation, login → account → logout, protected route redirect.

## Architecture

See [`docs/superpowers/specs/2026-05-06-probalab-v2-relaunch-design.md`](../docs/superpowers/specs/2026-05-06-probalab-v2-relaunch-design.md).

P1 (this commit batch) covers : skeleton + design tokens + auth shell. Pages métier come in P2.

## Project structure

```
src/
├── lib/                  # Supabase client, API fetcher, utils
├── contexts/             # AuthContext (session state)
├── hooks/                # useAuth + future useMatch, usePicks, etc.
├── components/
│   ├── ui/               # shadcn primitives (button, input, dialog, …)
│   ├── layout/           # Shell (Header, Footer, MobileNav, AppShell)
│   └── shared/           # ErrorBoundary, ProtectedRoute, Spinners
├── pages/                # Route-level components
├── styles/               # globals.css + tokens.css
├── types/                # env types
└── routes.tsx            # Route table
```

## Deployment

Vercel project name: `probalab-web`. SPA rewrite via `vercel.json`. Preview only in P1 (no DNS switch yet — that's P6).
