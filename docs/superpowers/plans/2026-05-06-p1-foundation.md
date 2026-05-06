# P1 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap a brand-new `web/` Vite + React 19 + TS + Tailwind 4 + shadcn project at the project root, wire up a proper design system, build a functional auth flow against the existing Supabase project, ship a deployable Vercel app that login/logout works end-to-end with a clean dark-mode shell.

**Architecture:** Greenfield Vite SPA built in parallel with the existing `ProbaLab/dashboard/` (which stays in production untouched). Uses the same backend (`ProbaLab/api/`) and same Supabase project (auth + DB). Design tokens defined as CSS variables consumed by Tailwind; shadcn components installed via CLI into `src/components/ui/`. Auth handled client-side via `@supabase/supabase-js`, JWT forwarded to FastAPI for downstream API calls. No premium gating or business pages yet — that's P2 and P3.

**Tech Stack:** Vite 7, React 19, TypeScript 5.7, Tailwind CSS 4, Radix UI, shadcn/ui, Framer Motion 12, react-router-dom 7, @tanstack/react-query 5, @supabase/supabase-js 2, lucide-react, clsx + tailwind-merge, Vitest 4 + Testing Library 16, Playwright 1.59, ESLint 9.

**Spec reference:** [docs/superpowers/specs/2026-05-06-probalab-v2-relaunch-design.md](../specs/2026-05-06-probalab-v2-relaunch-design.md) — sections §6 (architecture frontend), §11 (onboarding flow — modèle d'écran de redirection seulement, pas d'implémentation onboarding ici), §16 (points de vigilance).

**Out of scope for P1 (covered by later sub-plans):**
- Pages métier (home, picks, match, performance) → P2
- Premium gating, Stripe, paywall components → P3
- Onboarding modal + tooltips + user_preferences table → P4
- Bankroll tracker → P5
- SEO pages and cutover → P6

---

## File Structure

P1 creates the `web/` folder at the **repo root** (sibling of `ProbaLab/`, `docs/`, `.github/`). Layout:

```
web/
├── .env.example              # Template documenté des env vars VITE_*
├── .gitignore                # node_modules, dist, etc.
├── .nvmrc                    # node version pinned (20)
├── README.md                 # Bootstrap instructions
├── eslint.config.js          # ESLint flat config (React + TS)
├── index.html                # Entry HTML
├── package.json              # Manifest + scripts
├── playwright.config.ts      # E2E config (chromium + firefox)
├── postcss.config.js         # Tailwind v4 PostCSS plugin
├── tailwind.config.ts        # Tailwind v4 config + tokens reference
├── tsconfig.json             # TS strict mode
├── tsconfig.node.json        # TS for vite/playwright config files
├── vercel.json               # Vercel SPA rewrites
├── vite.config.ts            # Vite + plugin-react + path aliases
├── vitest.config.ts          # Unit test config
├── components.json           # shadcn config
├── public/
│   ├── favicon.svg
│   └── robots.txt            # Allow all (no SEO yet — will be replaced in P6)
├── src/
│   ├── main.tsx              # ReactDOM + StrictMode
│   ├── App.tsx               # Router + providers
│   ├── routes.tsx            # Route table (single source of truth)
│   ├── env.ts                # Typed import.meta.env validator (zod)
│   ├── lib/
│   │   ├── cn.ts             # clsx + tailwind-merge
│   │   ├── supabase.ts       # Supabase client singleton
│   │   └── api.ts            # fetch wrapper that injects Supabase JWT
│   ├── contexts/
│   │   └── AuthContext.tsx   # session state + login/logout/signup methods
│   ├── hooks/
│   │   └── useAuth.ts        # consumes AuthContext
│   ├── components/
│   │   ├── ui/               # shadcn components (button, input, dialog, etc.)
│   │   ├── layout/
│   │   │   ├── AppShell.tsx  # header + main + footer wrapper
│   │   │   ├── Header.tsx    # logo, nav skeleton, user menu
│   │   │   ├── MobileNav.tsx # bottom tabs
│   │   │   └── Footer.tsx
│   │   └── shared/
│   │       ├── ErrorBoundary.tsx     # root error boundary (lesson 79)
│   │       ├── LoadingSpinner.tsx
│   │       └── ProtectedRoute.tsx    # redirect to /auth/login if not logged
│   ├── pages/
│   │   ├── HomePage.tsx              # placeholder ("V1 in construction")
│   │   ├── auth/
│   │   │   ├── SignupPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   └── CallbackPage.tsx      # OAuth callback handler
│   │   ├── account/
│   │   │   └── AccountPage.tsx       # placeholder (logged in landing)
│   │   ├── NotFoundPage.tsx
│   │   └── ErrorPage.tsx
│   ├── styles/
│   │   ├── globals.css       # Tailwind directives + design tokens (CSS vars)
│   │   └── tokens.css        # Design tokens (colors, spacing, radii, fonts)
│   └── types/
│       └── env.d.ts          # ImportMeta.env types
├── tests/
│   ├── setup.ts              # vitest globals + jsdom
│   └── components/
│       ├── AuthContext.test.tsx
│       ├── ErrorBoundary.test.tsx
│       └── ProtectedRoute.test.tsx
└── e2e/
    ├── helpers/
    │   └── test-user.ts      # create / cleanup test user via Supabase admin
    ├── auth-signup.spec.ts
    └── auth-login-logout.spec.ts
```

**File responsibilities cheat sheet:**

| File | Responsibility |
|---|---|
| `web/vite.config.ts` | Build config, path alias `@/*` → `src/*`, dev server proxy `/api` → backend |
| `web/src/env.ts` | Validate at boot that all required `VITE_*` env vars are present (zod schema) |
| `web/src/lib/supabase.ts` | Create and export single Supabase client instance (no React) |
| `web/src/lib/api.ts` | `apiFetch(path, init?)` — adds `Authorization: Bearer <jwt>` from current Supabase session, throws typed errors |
| `web/src/contexts/AuthContext.tsx` | Holds `session`, `user`, `loading`; methods `signUp`, `signIn`, `signInWithGoogle`, `signOut`; subscribes to Supabase auth events |
| `web/src/components/shared/ProtectedRoute.tsx` | Wraps a route element; redirects to `/auth/login` if no session, with `?next=<currentPath>` |
| `web/src/components/layout/AppShell.tsx` | Provides the shell (header + content area + footer + mobile bottom nav). Used by all logged-in pages |
| `web/src/components/shared/ErrorBoundary.tsx` | Class component; catches render errors anywhere below; logs and renders `<ErrorPage />` |
| `web/src/styles/tokens.css` | Single source of truth for design tokens as CSS vars consumed by Tailwind config |

---

## Decisions baked into P1

These are decisions taken now to avoid bikeshedding mid-execution. They can be revisited in later plans if needed.

1. **Path alias** : `@/*` → `web/src/*`. Standard shadcn convention. Set in both `tsconfig.json` and `vite.config.ts`.
2. **CSS-in-CSS via tokens.css** : design tokens are CSS variables, not JS objects. Tailwind v4 reads them from `@theme` blocks. Pattern recommended by Tailwind v4 docs.
3. **Auth provider boundary** : `AuthContext` lives **inside** `<BrowserRouter>` so navigation works after login. Single source of session truth via `supabase.auth.onAuthStateChange`.
4. **API JWT injection** : `apiFetch` reads JWT from `supabase.auth.getSession()` at every call (no manual cache — Supabase handles refresh internally). If no session, the call is sent without `Authorization` header (let backend decide).
5. **No global Zustand/Redux** : React Query handles server state, AuthContext handles auth state. No client state framework needed in P1.
6. **No SSR/SSG yet** : pure SPA. SSG comes in P6 for SEO pages. Vercel `vercel.json` has SPA rewrite (`/*` → `/index.html`).
7. **No Sentry yet** : ErrorBoundary logs to `console.error`. Sentry wiring is in P3 (when paying customers exist and observability matters more).
8. **Test backend strategy** : E2E tests create users via Supabase service role API (using a test-only `SUPABASE_SERVICE_ROLE_KEY` env var). Cleanup deletes them after each spec.
9. **No analytics** : PostHog/Plausible decision deferred to P3 (when conversion funnel matters).
10. **Vercel deploy target** : preview-only in P1 (no DNS switch). Project name : `probalab-web` to avoid clashing with existing `probalab-dashboard`.

---

## Pre-flight checks

- [ ] **Step 0.1: Verify Node version**

Run: `node --version`
Expected: `v20.x.x` or higher. If not, install via `nvm install 20 && nvm use 20`.

- [ ] **Step 0.2: Verify pnpm or npm available**

We use **npm** (matches the existing `dashboard/`).
Run: `npm --version`
Expected: `>= 10.x`.

- [ ] **Step 0.3: Verify git working tree is clean**

Run: `git status`
Expected: clean (or only untracked files unrelated to `web/`).

- [ ] **Step 0.4: Confirm we're in the right worktree**

Run: `pwd && git branch --show-current`
Expected:
```
/Users/pierrelaurent/Desktop/Pierre/Projets Dev Pierre/ProbaLab/.claude/worktrees/busy-blackburn-0ee195
claude/busy-blackburn-0ee195
```

- [ ] **Step 0.5: Confirm Supabase env vars are reachable**

Read the existing dashboard env example for reference values:
```bash
cat ProbaLab/dashboard/.env.example
```
You should see `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`. We'll reuse the same Supabase project.

---

## Task 1 — Initialize Vite project skeleton

**Files:**
- Create: `web/package.json`
- Create: `web/vite.config.ts`
- Create: `web/tsconfig.json`
- Create: `web/tsconfig.node.json`
- Create: `web/index.html`
- Create: `web/.nvmrc`
- Create: `web/.gitignore`
- Create: `web/src/main.tsx`
- Create: `web/src/App.tsx`
- Create: `web/src/types/env.d.ts`

- [ ] **Step 1.1: Create `web/` directory and `.nvmrc`**

```bash
mkdir -p web
echo "20" > web/.nvmrc
```

- [ ] **Step 1.2: Write `web/.gitignore`**

```bash
cat > web/.gitignore <<'EOF'
node_modules/
dist/
.env
.env.local
.env.*.local
*.log
.DS_Store
playwright-report/
test-results/
coverage/
EOF
```

- [ ] **Step 1.3: Write `web/package.json`**

```json
{
  "name": "probalab-web",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "typecheck": "tsc -b --noEmit",
    "test": "vitest",
    "test:ci": "vitest run",
    "test:coverage": "vitest run --coverage",
    "e2e": "playwright test",
    "e2e:ui": "playwright test --ui"
  },
  "dependencies": {
    "@hookform/resolvers": "^5.2.2",
    "@radix-ui/react-avatar": "^1.1.11",
    "@radix-ui/react-dialog": "^1.1.18",
    "@radix-ui/react-dropdown-menu": "^2.1.18",
    "@radix-ui/react-scroll-area": "^1.2.10",
    "@radix-ui/react-separator": "^1.1.8",
    "@radix-ui/react-slot": "^1.2.4",
    "@radix-ui/react-tabs": "^1.1.13",
    "@radix-ui/react-toast": "^1.2.18",
    "@radix-ui/react-tooltip": "^1.2.8",
    "@supabase/supabase-js": "^2.45.0",
    "@tanstack/react-query": "^5.96.2",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "framer-motion": "^12.38.0",
    "lucide-react": "^0.563.0",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "react-hook-form": "^7.73.1",
    "react-router-dom": "^7.13.0",
    "tailwind-merge": "^3.4.0",
    "zod": "^4.3.6"
  },
  "devDependencies": {
    "@eslint/js": "^9.39.1",
    "@playwright/test": "^1.59.1",
    "@tailwindcss/postcss": "^4.1.18",
    "@testing-library/jest-dom": "^6.9.1",
    "@testing-library/react": "^16.3.2",
    "@testing-library/user-event": "^14.6.1",
    "@types/node": "^22.10.0",
    "@types/react": "^19.2.7",
    "@types/react-dom": "^19.2.3",
    "@vitejs/plugin-react": "^5.1.1",
    "@vitest/coverage-v8": "^4.1.2",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.39.1",
    "eslint-plugin-react-hooks": "^7.0.1",
    "eslint-plugin-react-refresh": "^0.4.24",
    "globals": "^16.5.0",
    "jsdom": "^29.0.1",
    "postcss": "^8.4.49",
    "tailwindcss": "^4.1.18",
    "typescript": "^5.7.0",
    "typescript-eslint": "^8.18.0",
    "vite": "^7.3.1",
    "vitest": "^4.1.2"
  }
}
```

- [ ] **Step 1.4: Write `web/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": false,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    },
    "types": ["vite/client", "vitest/globals", "@testing-library/jest-dom"]
  },
  "include": ["src", "tests"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 1.5: Write `web/tsconfig.node.json`**

```json
{
  "compilerOptions": {
    "target": "ES2023",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "noEmit": true,
    "types": ["node"]
  },
  "include": ["vite.config.ts", "vitest.config.ts", "playwright.config.ts", "eslint.config.js"]
}
```

- [ ] **Step 1.6: Write `web/vite.config.ts`**

```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

- [ ] **Step 1.7: Write `web/index.html`**

```html
<!doctype html>
<html lang="fr" class="dark">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#0a0a0a" />
    <title>ProbaLab — Probabilités sportives</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 1.8: Write `web/src/types/env.d.ts`**

```ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SUPABASE_URL: string;
  readonly VITE_SUPABASE_ANON_KEY: string;
  readonly VITE_API_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

- [ ] **Step 1.9: Write minimal `web/src/main.tsx`**

```tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles/globals.css';

createRoot(document.getElementById('root') as HTMLElement).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

- [ ] **Step 1.10: Write minimal `web/src/App.tsx`**

```tsx
export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
      <h1 className="text-2xl font-bold">ProbaLab — Foundation OK</h1>
    </div>
  );
}
```

- [ ] **Step 1.11: Install dependencies**

```bash
cd web && npm install
```

Expected: install succeeds with no peer-dep errors. If lockfile conflicts emerge with later versions of React 19 packages, accept the lockfile generated by `npm install` (no `--legacy-peer-deps` unless strictly required — log it as a follow-up if needed).

- [ ] **Step 1.12: Verify TypeScript compiles**

Run: `cd web && npm run typecheck`
Expected: exit 0, no output (or warnings only). If it fails because `globals.css` doesn't exist yet, create an empty file:
```bash
mkdir -p web/src/styles && touch web/src/styles/globals.css
```
Then re-run.

- [ ] **Step 1.13: Smoke test — dev server boots**

Run: `cd web && npm run dev`
Expected: Vite logs "Local: http://localhost:5173/" within 3s. Stop with Ctrl+C.

- [ ] **Step 1.14: Commit**

```bash
git add web/ && git commit -m "$(cat <<'EOF'
feat(web/p1): initialize Vite + React 19 + TS skeleton

- Empty Vite SPA at web/ with React 19, TS strict, path alias @/* → src/*
- Dev server proxy /api → localhost:8000 (FastAPI backend)
- Independent of existing ProbaLab/dashboard/ — built in parallel

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2 — Tailwind CSS 4 + design tokens

**Files:**
- Create: `web/postcss.config.js`
- Create: `web/tailwind.config.ts`
- Create: `web/src/styles/tokens.css`
- Modify: `web/src/styles/globals.css`
- Modify: `web/src/App.tsx` (smoke test the tokens)

- [ ] **Step 2.1: Write `web/postcss.config.js`**

```js
export default {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 2.2: Write `web/src/styles/tokens.css`**

Single source of truth for design tokens. Dark-mode-first (we ship dark by default, light values are placeholders for V2 if needed).

```css
@layer base {
  :root {
    /* Surfaces */
    --background: 0 0% 4%;          /* #0a0a0a */
    --foreground: 0 0% 98%;         /* near-white */
    --card: 0 0% 6%;                /* #0f0f0f */
    --card-foreground: 0 0% 96%;
    --popover: 0 0% 8%;
    --popover-foreground: 0 0% 96%;

    /* Primary brand (cool indigo/violet — premium) */
    --primary: 256 80% 65%;         /* purple-violet */
    --primary-foreground: 0 0% 100%;

    /* Accents semantic */
    --success: 142 76% 56%;         /* green-400 */
    --success-foreground: 0 0% 4%;
    --warning: 38 92% 60%;          /* amber-400 */
    --warning-foreground: 0 0% 4%;
    --danger: 0 84% 60%;            /* red-500 */
    --danger-foreground: 0 0% 100%;

    /* Borders / muted */
    --muted: 0 0% 12%;
    --muted-foreground: 0 0% 60%;
    --border: 0 0% 16%;
    --input: 0 0% 12%;
    --ring: 256 80% 65%;

    /* Radius */
    --radius: 0.5rem;

    /* Type */
    --font-sans: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Inter", sans-serif;
    --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  }
}
```

- [ ] **Step 2.3: Write `web/tailwind.config.ts`**

```ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        success: {
          DEFAULT: 'hsl(var(--success))',
          foreground: 'hsl(var(--success-foreground))',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning))',
          foreground: 'hsl(var(--warning-foreground))',
        },
        danger: {
          DEFAULT: 'hsl(var(--danger))',
          foreground: 'hsl(var(--danger-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      fontFamily: {
        sans: 'var(--font-sans)',
        mono: 'var(--font-mono)',
      },
    },
  },
};

export default config;
```

- [ ] **Step 2.4: Write `web/src/styles/globals.css`**

```css
@import "tailwindcss";
@import "./tokens.css";

@layer base {
  * {
    border-color: hsl(var(--border));
  }
  html, body, #root {
    height: 100%;
  }
  body {
    background-color: hsl(var(--background));
    color: hsl(var(--foreground));
    font-family: var(--font-sans);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
}
```

- [ ] **Step 2.5: Update `web/src/App.tsx` to smoke-test tokens**

```tsx
export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <main className="mx-auto max-w-2xl px-6 py-16 space-y-6">
        <h1 className="text-3xl font-bold">ProbaLab — Foundation</h1>
        <p className="text-muted-foreground">
          Si vous voyez ce texte avec un fond noir, le fond muted plus clair, et les boutons colorés en dessous, le design system est OK.
        </p>
        <div className="flex flex-wrap gap-3">
          <button className="rounded-md bg-primary px-4 py-2 font-medium text-primary-foreground">Primary</button>
          <button className="rounded-md bg-success px-4 py-2 font-medium text-success-foreground">Success</button>
          <button className="rounded-md bg-warning px-4 py-2 font-medium text-warning-foreground">Warning</button>
          <button className="rounded-md bg-danger px-4 py-2 font-medium text-danger-foreground">Danger</button>
          <div className="rounded-md border border-border bg-card px-4 py-2 text-card-foreground">Card surface</div>
        </div>
      </main>
    </div>
  );
}
```

- [ ] **Step 2.6: Verify dev server renders correctly**

Run: `cd web && npm run dev`
Open http://localhost:5173 in a browser.
Expected: black background, white text, 4 colored buttons (purple/green/amber/red) and a card surface. Stop with Ctrl+C.

- [ ] **Step 2.7: Verify build passes**

Run: `cd web && npm run build`
Expected: build succeeds, `dist/` folder created. The output should include `index.html` and `assets/index-*.css` containing the Tailwind output.

- [ ] **Step 2.8: Commit**

```bash
git add web/ && git commit -m "$(cat <<'EOF'
feat(web/p1): wire Tailwind 4 + design tokens (dark-first)

- tokens.css holds CSS vars (HSL) for surfaces, brand, semantic accents
- tailwind.config.ts maps tokens to Tailwind utility colors
- globals.css imports tailwindcss + tokens + base reset
- App.tsx smoke-tests primary/success/warning/danger buttons + card

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3 — ESLint + Prettier-equivalent flat config

**Files:**
- Create: `web/eslint.config.js`
- Modify: `web/src/App.tsx` (no lint errors)

- [ ] **Step 3.1: Write `web/eslint.config.js`**

```js
import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist', 'playwright-report', 'test-results', 'coverage'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    },
  }
);
```

- [ ] **Step 3.2: Run lint to confirm no errors**

Run: `cd web && npm run lint`
Expected: exit 0, no errors. (Possibly some `react-refresh` warnings on `App.tsx` because it exports a non-component along with the default — fine for now, will resolve as we add proper structure.)

- [ ] **Step 3.3: Commit**

```bash
git add web/eslint.config.js && git commit -m "$(cat <<'EOF'
chore(web/p1): add ESLint flat config (TS + React hooks)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4 — Vitest + Testing Library setup

**Files:**
- Create: `web/vitest.config.ts`
- Create: `web/tests/setup.ts`
- Create: `web/tests/components/sanity.test.tsx`

- [ ] **Step 4.1: Write `web/vitest.config.ts`**

```ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.test.{ts,tsx}'],
    css: false,
  },
});
```

- [ ] **Step 4.2: Write `web/tests/setup.ts`**

```ts
import '@testing-library/jest-dom/vitest';
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

afterEach(() => {
  cleanup();
});
```

- [ ] **Step 4.3: Write a sanity test `web/tests/components/sanity.test.tsx`**

```tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

function Greeting({ name }: { name: string }) {
  return <p>Hello, {name}!</p>;
}

describe('Test setup sanity', () => {
  it('renders a component and finds text', () => {
    render(<Greeting name="ProbaLab" />);
    expect(screen.getByText('Hello, ProbaLab!')).toBeInTheDocument();
  });
});
```

- [ ] **Step 4.4: Run test to verify it passes**

Run: `cd web && npm run test:ci`
Expected: 1 test, 1 pass.

- [ ] **Step 4.5: Commit**

```bash
git add web/ && git commit -m "$(cat <<'EOF'
test(web/p1): add Vitest + Testing Library setup with sanity test

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5 — Env validation with zod

**Files:**
- Create: `web/.env.example`
- Create: `web/src/env.ts`
- Create: `web/tests/env.test.ts`
- Modify: `web/src/main.tsx` (call validateEnv)

- [ ] **Step 5.1: Write `web/.env.example`**

```bash
# Supabase (frontend public credentials — anon key only, NEVER service_role here)
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOi...

# Backend FastAPI URL
VITE_API_URL=http://localhost:8000
```

- [ ] **Step 5.2: Write the failing test `web/tests/env.test.ts`**

```ts
import { describe, it, expect } from 'vitest';
import { z } from 'zod';
import { envSchema } from '@/env';

describe('envSchema', () => {
  it('accepts a valid env object', () => {
    const result = envSchema.safeParse({
      VITE_SUPABASE_URL: 'https://test.supabase.co',
      VITE_SUPABASE_ANON_KEY: 'eyJtest',
      VITE_API_URL: 'http://localhost:8000',
    });
    expect(result.success).toBe(true);
  });

  it('rejects an env object missing VITE_SUPABASE_URL', () => {
    const result = envSchema.safeParse({
      VITE_SUPABASE_ANON_KEY: 'eyJtest',
      VITE_API_URL: 'http://localhost:8000',
    });
    expect(result.success).toBe(false);
  });

  it('rejects a non-URL VITE_SUPABASE_URL', () => {
    const result = envSchema.safeParse({
      VITE_SUPABASE_URL: 'not-a-url',
      VITE_SUPABASE_ANON_KEY: 'eyJtest',
      VITE_API_URL: 'http://localhost:8000',
    });
    expect(result.success).toBe(false);
  });

  it('exports the inferred Env type', () => {
    type Env = z.infer<typeof envSchema>;
    const e: Env = {
      VITE_SUPABASE_URL: 'https://x.co',
      VITE_SUPABASE_ANON_KEY: 'k',
      VITE_API_URL: 'http://l',
    };
    expect(e.VITE_API_URL).toBeDefined();
  });
});
```

- [ ] **Step 5.3: Run test to verify it fails**

Run: `cd web && npm run test:ci -- tests/env.test.ts`
Expected: FAIL — module `@/env` does not exist.

- [ ] **Step 5.4: Write `web/src/env.ts`**

```ts
import { z } from 'zod';

export const envSchema = z.object({
  VITE_SUPABASE_URL: z.string().url(),
  VITE_SUPABASE_ANON_KEY: z.string().min(10),
  VITE_API_URL: z.string().url(),
});

export type Env = z.infer<typeof envSchema>;

let cachedEnv: Env | null = null;

export function validateEnv(): Env {
  if (cachedEnv) return cachedEnv;
  const result = envSchema.safeParse(import.meta.env);
  if (!result.success) {
    const message = `Invalid frontend env vars:\n${JSON.stringify(result.error.flatten().fieldErrors, null, 2)}`;
    throw new Error(message);
  }
  cachedEnv = result.data;
  return cachedEnv;
}
```

- [ ] **Step 5.5: Run test to verify it passes**

Run: `cd web && npm run test:ci -- tests/env.test.ts`
Expected: 4 tests, 4 pass.

- [ ] **Step 5.6: Update `web/src/main.tsx` to call validateEnv at boot**

```tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { validateEnv } from './env';
import './styles/globals.css';

// Fail fast at boot if env vars are missing or malformed.
validateEnv();

createRoot(document.getElementById('root') as HTMLElement).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

- [ ] **Step 5.7: Verify dev server still boots if .env is present**

Create `web/.env.local` with real values:
```bash
cp web/.env.example web/.env.local
# Edit web/.env.local with actual VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY values
# (copy them from the existing ProbaLab/dashboard/.env.local if you have it locally)
```

Then run `cd web && npm run dev`. Expected: dev server boots, app renders. If env is missing, the page should crash with a clear error message in the browser console.

- [ ] **Step 5.8: Commit**

```bash
git add web/ && git commit -m "$(cat <<'EOF'
feat(web/p1): validate frontend env vars at boot via zod

- src/env.ts exposes envSchema + validateEnv()
- main.tsx calls validateEnv() before mounting React
- Fail-fast with clear field-level error message

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6 — Supabase client + JWT-aware API client

**Files:**
- Create: `web/src/lib/supabase.ts`
- Create: `web/src/lib/api.ts`
- Create: `web/src/lib/cn.ts`
- Create: `web/tests/lib/api.test.ts`

- [ ] **Step 6.1: Write `web/src/lib/supabase.ts`**

```ts
import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import { validateEnv } from '@/env';

let client: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient {
  if (client) return client;
  const env = validateEnv();
  client = createClient(env.VITE_SUPABASE_URL, env.VITE_SUPABASE_ANON_KEY, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });
  return client;
}
```

- [ ] **Step 6.2: Write `web/src/lib/cn.ts`**

```ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 6.3: Write the failing test `web/tests/lib/api.test.ts`**

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiFetch, ApiError } from '@/lib/api';

const getSessionMock = vi.fn();
vi.mock('@/lib/supabase', () => ({
  getSupabase: () => ({
    auth: {
      getSession: getSessionMock,
    },
  }),
}));

vi.mock('@/env', () => ({
  validateEnv: () => ({
    VITE_API_URL: 'http://api.test',
    VITE_SUPABASE_URL: 'http://sb.test',
    VITE_SUPABASE_ANON_KEY: 'anon',
  }),
}));

describe('apiFetch', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    getSessionMock.mockReset();
  });

  it('attaches Authorization header when session exists', async () => {
    getSessionMock.mockResolvedValue({ data: { session: { access_token: 'jwt-abc' } } });
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200, headers: { 'content-type': 'application/json' } })
    );

    const data = await apiFetch<{ ok: boolean }>('/api/v2/home');

    expect(data).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/api/v2/home',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer jwt-abc' }),
      })
    );
  });

  it('omits Authorization when no session', async () => {
    getSessionMock.mockResolvedValue({ data: { session: null } });
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200, headers: { 'content-type': 'application/json' } })
    );

    await apiFetch('/api/v2/home');

    const call = fetchMock.mock.calls[0];
    const headers = call[1]?.headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
  });

  it('throws ApiError with status on non-2xx response', async () => {
    getSessionMock.mockResolvedValue({ data: { session: null } });
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Not found' }), {
        status: 404,
        headers: { 'content-type': 'application/json' },
      })
    );

    await expect(apiFetch('/api/v2/match/x')).rejects.toMatchObject({
      name: 'ApiError',
      status: 404,
    });
  });

  it('returns text when content-type is not JSON', async () => {
    getSessionMock.mockResolvedValue({ data: { session: null } });
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('plain text', { status: 200, headers: { 'content-type': 'text/plain' } })
    );

    const data = await apiFetch<string>('/api/healthz');
    expect(data).toBe('plain text');
  });

  it('ApiError class is thrown correctly', async () => {
    getSessionMock.mockResolvedValue({ data: { session: null } });
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('{}', { status: 500, headers: { 'content-type': 'application/json' } })
    );

    try {
      await apiFetch('/api/x');
      expect.fail('Should have thrown');
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).status).toBe(500);
    }
  });
});
```

- [ ] **Step 6.4: Run test to verify it fails**

Run: `cd web && npm run test:ci -- tests/lib/api.test.ts`
Expected: FAIL — module `@/lib/api` does not exist.

- [ ] **Step 6.5: Write `web/src/lib/api.ts`**

```ts
import { getSupabase } from '@/lib/supabase';
import { validateEnv } from '@/env';

export class ApiError extends Error {
  override readonly name = 'ApiError';
  constructor(
    message: string,
    public readonly status: number,
    public readonly body: unknown
  ) {
    super(message);
  }
}

export async function apiFetch<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const env = validateEnv();
  const url = `${env.VITE_API_URL}${path}`;

  const supabase = getSupabase();
  const { data: { session } } = await supabase.auth.getSession();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((init.headers as Record<string, string>) ?? {}),
  };
  if (session?.access_token) {
    headers.Authorization = `Bearer ${session.access_token}`;
  }

  const response = await fetch(url, { ...init, headers });

  if (!response.ok) {
    const contentType = response.headers.get('content-type') ?? '';
    const body = contentType.includes('application/json') ? await response.json() : await response.text();
    throw new ApiError(`API error ${response.status} on ${path}`, response.status, body);
  }

  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return (await response.json()) as T;
  }
  return (await response.text()) as unknown as T;
}
```

- [ ] **Step 6.6: Run test to verify it passes**

Run: `cd web && npm run test:ci -- tests/lib/api.test.ts`
Expected: 5 tests, 5 pass.

- [ ] **Step 6.7: Verify all tests still pass**

Run: `cd web && npm run test:ci`
Expected: 7 tests total (sanity + env + api), all pass.

- [ ] **Step 6.8: Verify typecheck**

Run: `cd web && npm run typecheck`
Expected: exit 0.

- [ ] **Step 6.9: Commit**

```bash
git add web/ && git commit -m "$(cat <<'EOF'
feat(web/p1): add Supabase client + JWT-aware apiFetch + cn helper

- lib/supabase.ts exposes getSupabase() singleton (lazy)
- lib/api.ts apiFetch<T>() injects Bearer JWT from current session,
  throws ApiError with status on non-2xx, handles JSON/text responses
- lib/cn.ts wraps clsx + tailwind-merge

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7 — shadcn CLI init + first 3 components (button, input, dialog)

**Files:**
- Create: `web/components.json`
- Create: `web/src/components/ui/button.tsx`
- Create: `web/src/components/ui/input.tsx`
- Create: `web/src/components/ui/dialog.tsx`
- Create: `web/src/components/ui/label.tsx`
- Modify: `web/src/App.tsx` (smoke test)

- [ ] **Step 7.1: Write `web/components.json`**

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/styles/globals.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/cn",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "iconLibrary": "lucide"
}
```

- [ ] **Step 7.2: Write `web/src/components/ui/button.tsx`**

```tsx
import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/cn';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-danger text-danger-foreground hover:bg-danger/90',
        outline: 'border border-border bg-background hover:bg-muted hover:text-foreground',
        secondary: 'bg-muted text-foreground hover:bg-muted/80',
        ghost: 'hover:bg-muted hover:text-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return <Comp className={cn(buttonVariants({ variant, size }), className)} ref={ref} {...props} />;
  }
);
Button.displayName = 'Button';

export { buttonVariants };
```

- [ ] **Step 7.3: Write `web/src/components/ui/input.tsx`**

```tsx
import * as React from 'react';
import { cn } from '@/lib/cn';

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        'flex h-10 w-full rounded-md border border-border bg-input px-3 py-2 text-sm text-foreground ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      ref={ref}
      {...props}
    />
  );
});
Input.displayName = 'Input';
```

- [ ] **Step 7.4: Write `web/src/components/ui/label.tsx`**

```tsx
import * as React from 'react';
import { cn } from '@/lib/cn';

export const Label = React.forwardRef<HTMLLabelElement, React.LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn('text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70', className)}
      {...props}
    />
  )
);
Label.displayName = 'Label';
```

- [ ] **Step 7.5: Write `web/src/components/ui/dialog.tsx`**

```tsx
import * as React from 'react';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { cn } from '@/lib/cn';

const Dialog = DialogPrimitive.Root;
const DialogTrigger = DialogPrimitive.Trigger;
const DialogPortal = DialogPrimitive.Portal;
const DialogClose = DialogPrimitive.Close;

const DialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      'fixed inset-0 z-50 bg-background/80 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0',
      className
    )}
    {...props}
  />
));
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName;

const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        'fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border border-border bg-card p-6 shadow-lg duration-200 sm:rounded-lg',
        className
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring disabled:pointer-events-none">
        <X className="h-4 w-4" />
        <span className="sr-only">Fermer</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPortal>
));
DialogContent.displayName = DialogPrimitive.Content.displayName;

const DialogHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('flex flex-col space-y-1.5 text-center sm:text-left', className)} {...props} />
);
DialogHeader.displayName = 'DialogHeader';

const DialogTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn('text-lg font-semibold leading-none tracking-tight', className)}
    {...props}
  />
));
DialogTitle.displayName = DialogPrimitive.Title.displayName;

const DialogDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn('text-sm text-muted-foreground', className)}
    {...props}
  />
));
DialogDescription.displayName = DialogPrimitive.Description.displayName;

export {
  Dialog,
  DialogTrigger,
  DialogClose,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
};
```

- [ ] **Step 7.6: Update `web/src/App.tsx` to smoke-test shadcn**

```tsx
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <main className="mx-auto max-w-2xl px-6 py-16 space-y-8">
        <h1 className="text-3xl font-bold">ProbaLab — Foundation</h1>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold">Buttons</h2>
          <div className="flex flex-wrap gap-2">
            <Button>Default</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="destructive">Destructive</Button>
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold">Form fields</h2>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" placeholder="ton@email.fr" />
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold">Dialog</h2>
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="outline">Ouvrir un dialog</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Coucou</DialogTitle>
                <DialogDescription>
                  Ce dialog confirme que Radix + shadcn fonctionnent.
                </DialogDescription>
              </DialogHeader>
            </DialogContent>
          </Dialog>
        </section>
      </main>
    </div>
  );
}
```

- [ ] **Step 7.7: Verify dev server renders shadcn correctly**

Run: `cd web && npm run dev` and open http://localhost:5173.
Expected: 5 colored buttons, an email input, a dialog button. Click the dialog button → modal opens with overlay + close X. Stop with Ctrl+C.

- [ ] **Step 7.8: Verify typecheck and lint**

Run: `cd web && npm run typecheck && npm run lint`
Expected: both exit 0.

- [ ] **Step 7.9: Commit**

```bash
git add web/ && git commit -m "$(cat <<'EOF'
feat(web/p1): add first shadcn primitives (Button, Input, Label, Dialog)

- components.json declares shadcn config (new-york style, lucide icons)
- Button uses cva for variant/size matrix
- Dialog wraps Radix with backdrop blur + close X
- App.tsx smoke-tests all primitives

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8 — AuthContext + useAuth hook

**Files:**
- Create: `web/src/contexts/AuthContext.tsx`
- Create: `web/src/hooks/useAuth.ts`
- Create: `web/tests/contexts/AuthContext.test.tsx`

- [ ] **Step 8.1: Write the failing test `web/tests/contexts/AuthContext.test.tsx`**

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import { AuthProvider } from '@/contexts/AuthContext';
import { useAuth } from '@/hooks/useAuth';

const mockOnAuthStateChange = vi.fn();
const mockGetSession = vi.fn();
const mockSignInWithPassword = vi.fn();
const mockSignUp = vi.fn();
const mockSignOut = vi.fn();
const mockSignInWithOAuth = vi.fn();

vi.mock('@/lib/supabase', () => ({
  getSupabase: () => ({
    auth: {
      onAuthStateChange: mockOnAuthStateChange,
      getSession: mockGetSession,
      signInWithPassword: mockSignInWithPassword,
      signUp: mockSignUp,
      signOut: mockSignOut,
      signInWithOAuth: mockSignInWithOAuth,
    },
  }),
}));

function Probe() {
  const { user, loading } = useAuth();
  if (loading) return <p>loading</p>;
  return <p>{user ? `user:${user.id}` : 'anon'}</p>;
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockOnAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } });
  });

  it('starts in loading state then resolves to anon when no session', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    expect(screen.getByText('loading')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('anon')).toBeInTheDocument());
  });

  it('exposes user when an existing session is present', async () => {
    mockGetSession.mockResolvedValue({
      data: {
        session: {
          user: { id: 'u-1', email: 'a@b.fr' },
          access_token: 'tok',
        },
      },
    });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByText('user:u-1')).toBeInTheDocument());
  });

  it('updates state when onAuthStateChange fires SIGNED_IN', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });
    let cb: ((event: string, session: unknown) => void) | undefined;
    mockOnAuthStateChange.mockImplementation((handler) => {
      cb = handler;
      return { data: { subscription: { unsubscribe: vi.fn() } } };
    });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByText('anon')).toBeInTheDocument());

    act(() => {
      cb?.('SIGNED_IN', { user: { id: 'u-2', email: 'c@d.fr' }, access_token: 't' });
    });

    await waitFor(() => expect(screen.getByText('user:u-2')).toBeInTheDocument());
  });
});
```

- [ ] **Step 8.2: Run test to verify it fails**

Run: `cd web && npm run test:ci -- tests/contexts/AuthContext.test.tsx`
Expected: FAIL — modules don't exist.

- [ ] **Step 8.3: Write `web/src/contexts/AuthContext.tsx`**

```tsx
import { createContext, useEffect, useState, type ReactNode } from 'react';
import type { Session, User, AuthError } from '@supabase/supabase-js';
import { getSupabase } from '@/lib/supabase';

export interface AuthContextValue {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signUp: (email: string, password: string) => Promise<{ error: AuthError | null }>;
  signIn: (email: string, password: string) => Promise<{ error: AuthError | null }>;
  signInWithGoogle: (redirectTo?: string) => Promise<{ error: AuthError | null }>;
  signOut: () => Promise<{ error: AuthError | null }>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const supabase = getSupabase();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    supabase.auth.getSession().then(({ data }) => {
      if (!mounted) return;
      setSession(data.session ?? null);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession ?? null);
      setLoading(false);
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, [supabase]);

  const value: AuthContextValue = {
    user: session?.user ?? null,
    session,
    loading,
    signUp: async (email, password) => {
      const { error } = await supabase.auth.signUp({ email, password });
      return { error };
    },
    signIn: async (email, password) => {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      return { error };
    },
    signInWithGoogle: async (redirectTo) => {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: redirectTo ? { redirectTo } : undefined,
      });
      return { error };
    },
    signOut: async () => {
      const { error } = await supabase.auth.signOut();
      return { error };
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
```

- [ ] **Step 8.4: Write `web/src/hooks/useAuth.ts`**

```ts
import { useContext } from 'react';
import { AuthContext, type AuthContextValue } from '@/contexts/AuthContext';

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>');
  }
  return ctx;
}
```

- [ ] **Step 8.5: Run test to verify it passes**

Run: `cd web && npm run test:ci -- tests/contexts/AuthContext.test.tsx`
Expected: 3 tests, 3 pass.

- [ ] **Step 8.6: Verify all tests still pass**

Run: `cd web && npm run test:ci`
Expected: 11 tests total (sanity + env + api + AuthContext), all pass.

- [ ] **Step 8.7: Commit**

```bash
git add web/ && git commit -m "$(cat <<'EOF'
feat(web/p1): add AuthContext + useAuth hook (Supabase auth state)

- AuthContext subscribes to onAuthStateChange, exposes session/user/loading
- Methods: signUp, signIn, signInWithGoogle, signOut
- useAuth() throws if used outside provider (defensive)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9 — ErrorBoundary + ProtectedRoute

**Files:**
- Create: `web/src/components/shared/ErrorBoundary.tsx`
- Create: `web/src/components/shared/LoadingSpinner.tsx`
- Create: `web/src/components/shared/ProtectedRoute.tsx`
- Create: `web/src/pages/ErrorPage.tsx`
- Create: `web/tests/components/ErrorBoundary.test.tsx`
- Create: `web/tests/components/ProtectedRoute.test.tsx`

- [ ] **Step 9.1: Write `web/src/pages/ErrorPage.tsx`**

```tsx
import { Button } from '@/components/ui/button';

export default function ErrorPage({ error }: { error?: Error }) {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center px-6">
      <div className="max-w-md text-center space-y-4">
        <h1 className="text-2xl font-bold">Une erreur est survenue</h1>
        <p className="text-muted-foreground">
          Quelque chose s'est mal passé. L'équipe a été notifiée.
        </p>
        {error && import.meta.env.DEV && (
          <pre className="text-left text-xs text-muted-foreground bg-card p-3 rounded-md overflow-auto">
            {error.message}
          </pre>
        )}
        <Button onClick={() => window.location.assign('/')}>Retour à l'accueil</Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 9.2: Write `web/src/components/shared/LoadingSpinner.tsx`**

```tsx
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/cn';

export function LoadingSpinner({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center justify-center', className)}>
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  );
}

export function FullPageSpinner() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <LoadingSpinner />
    </div>
  );
}
```

- [ ] **Step 9.3: Write the failing test `web/tests/components/ErrorBoundary.test.tsx`**

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';

function Boom(): React.ReactElement {
  throw new Error('boom');
}

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <p>safe</p>
      </ErrorBoundary>
    );
    expect(screen.getByText('safe')).toBeInTheDocument();
  });

  it('renders ErrorPage when child throws', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>
    );
    expect(screen.getByText(/erreur est survenue/i)).toBeInTheDocument();
    spy.mockRestore();
  });
});
```

- [ ] **Step 9.4: Run test to verify it fails**

Run: `cd web && npm run test:ci -- tests/components/ErrorBoundary.test.tsx`
Expected: FAIL — module doesn't exist.

- [ ] **Step 9.5: Write `web/src/components/shared/ErrorBoundary.tsx`**

```tsx
import { Component, type ErrorInfo, type ReactNode } from 'react';
import ErrorPage from '@/pages/ErrorPage';

interface State {
  error: Error | null;
}

interface Props {
  children: ReactNode;
  fallback?: (error: Error) => ReactNode;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info);
  }

  render() {
    if (this.state.error) {
      if (this.props.fallback) return this.props.fallback(this.state.error);
      return <ErrorPage error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

- [ ] **Step 9.6: Run test to verify it passes**

Run: `cd web && npm run test:ci -- tests/components/ErrorBoundary.test.tsx`
Expected: 2 tests, 2 pass.

- [ ] **Step 9.7: Write the failing test `web/tests/components/ProtectedRoute.test.tsx`**

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/shared/ProtectedRoute';

const mockOnAuthStateChange = vi.fn();
const mockGetSession = vi.fn();

vi.mock('@/lib/supabase', () => ({
  getSupabase: () => ({
    auth: {
      onAuthStateChange: mockOnAuthStateChange,
      getSession: mockGetSession,
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
      signInWithOAuth: vi.fn(),
    },
  }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  mockOnAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } });
});

function setup(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <Routes>
          <Route path="/auth/login" element={<p>login page</p>} />
          <Route
            path="/account"
            element={
              <ProtectedRoute>
                <p>account content</p>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('ProtectedRoute', () => {
  it('renders children when user is authenticated', async () => {
    mockGetSession.mockResolvedValue({
      data: { session: { user: { id: 'u-1', email: 'a@b.fr' }, access_token: 't' } },
    });

    setup('/account');
    await waitFor(() => expect(screen.getByText('account content')).toBeInTheDocument());
  });

  it('redirects to /auth/login when user is anonymous', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });

    setup('/account');
    await waitFor(() => expect(screen.getByText('login page')).toBeInTheDocument());
  });
});
```

- [ ] **Step 9.8: Run test to verify it fails**

Run: `cd web && npm run test:ci -- tests/components/ProtectedRoute.test.tsx`
Expected: FAIL — module doesn't exist.

- [ ] **Step 9.9: Write `web/src/components/shared/ProtectedRoute.tsx`**

```tsx
import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { FullPageSpinner } from '@/components/shared/LoadingSpinner';

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <FullPageSpinner />;
  if (!user) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/auth/login?next=${next}`} replace />;
  }
  return <>{children}</>;
}
```

- [ ] **Step 9.10: Run test to verify it passes**

Run: `cd web && npm run test:ci -- tests/components/ProtectedRoute.test.tsx`
Expected: 2 tests, 2 pass.

- [ ] **Step 9.11: Verify all tests still pass**

Run: `cd web && npm run test:ci`
Expected: 15 tests total, all pass.

- [ ] **Step 9.12: Commit**

```bash
git add web/ && git commit -m "$(cat <<'EOF'
feat(web/p1): add ErrorBoundary + ProtectedRoute + Spinner + ErrorPage

- ErrorBoundary class component catches render errors, renders ErrorPage
- ProtectedRoute redirects to /auth/login?next=... when no session
- LoadingSpinner + FullPageSpinner via Loader2 (lucide)
- ErrorPage shows friendly message + dev-only stack

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10 — Layout shell (Header, Footer, MobileNav, AppShell)

**Files:**
- Create: `web/public/favicon.svg`
- Create: `web/src/components/layout/Header.tsx`
- Create: `web/src/components/layout/Footer.tsx`
- Create: `web/src/components/layout/MobileNav.tsx`
- Create: `web/src/components/layout/AppShell.tsx`

- [ ] **Step 10.1: Write `web/public/favicon.svg`**

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#0a0a0a"/>
  <path d="M8 22 L8 10 L14 10 Q18 10 18 14 Q18 18 14 18 L11 18 L11 22 Z M11 13 L11 15 L14 15 Q15 15 15 14 Q15 13 14 13 Z" fill="hsl(256, 80%, 65%)"/>
  <circle cx="22" cy="20" r="2.5" fill="hsl(142, 76%, 56%)"/>
</svg>
```

- [ ] **Step 10.2: Write `web/src/components/layout/Header.tsx`**

```tsx
import { Link, NavLink } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/cn';
import { Zap } from 'lucide-react';

const NAV_ITEMS: { to: string; label: string }[] = [
  { to: '/', label: 'Accueil' },
];

export function Header() {
  const { user, signOut } = useAuth();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-14 flex items-center gap-4">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <Zap className="h-5 w-5 text-primary" />
          <span>ProbaLab</span>
        </Link>

        <nav className="hidden md:flex items-center gap-1 ml-4">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                  isActive ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground'
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          {user ? (
            <>
              <span className="hidden sm:inline text-sm text-muted-foreground truncate max-w-[180px]">
                {user.email}
              </span>
              <Button size="sm" variant="outline" onClick={() => void signOut()}>
                Déconnexion
              </Button>
            </>
          ) : (
            <>
              <Button size="sm" variant="ghost" asChild>
                <Link to="/auth/login">Connexion</Link>
              </Button>
              <Button size="sm" asChild>
                <Link to="/auth/signup">Inscription</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
```

- [ ] **Step 10.3: Write `web/src/components/layout/Footer.tsx`**

```tsx
import { Link } from 'react-router-dom';

export function Footer() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 text-sm text-muted-foreground">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <p>&copy; 2026 ProbaLab. Plateforme d'analyse probabiliste sportive.</p>
          <nav className="flex flex-wrap gap-4">
            <Link to="/legal/mentions" className="hover:text-foreground">Mentions légales</Link>
            <Link to="/legal/cgu" className="hover:text-foreground">CGU</Link>
            <Link to="/legal/jeu-responsable" className="hover:text-foreground">Jeu responsable</Link>
          </nav>
        </div>
      </div>
    </footer>
  );
}
```

- [ ] **Step 10.4: Write `web/src/components/layout/MobileNav.tsx`**

```tsx
import { NavLink } from 'react-router-dom';
import { Home, User } from 'lucide-react';
import { cn } from '@/lib/cn';
import { useAuth } from '@/hooks/useAuth';

const ITEMS = [
  { to: '/', label: 'Accueil', icon: Home },
];

export function MobileNav() {
  const { user } = useAuth();
  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 border-t border-border bg-background/95 backdrop-blur">
      <div className="flex items-stretch justify-around h-14">
        {ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex-1 flex flex-col items-center justify-center gap-0.5 text-xs',
                isActive ? 'text-foreground' : 'text-muted-foreground'
              )
            }
          >
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
        <NavLink
          to={user ? '/account' : '/auth/login'}
          className={({ isActive }) =>
            cn(
              'flex-1 flex flex-col items-center justify-center gap-0.5 text-xs',
              isActive ? 'text-foreground' : 'text-muted-foreground'
            )
          }
        >
          <User className="h-5 w-5" />
          {user ? 'Compte' : 'Connexion'}
        </NavLink>
      </div>
    </nav>
  );
}
```

- [ ] **Step 10.5: Write `web/src/components/layout/AppShell.tsx`**

```tsx
import type { ReactNode } from 'react';
import { Header } from './Header';
import { Footer } from './Footer';
import { MobileNav } from './MobileNav';

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <Header />
      <main className="flex-1 pb-16 md:pb-0">{children}</main>
      <Footer />
      <MobileNav />
    </div>
  );
}
```

- [ ] **Step 10.6: Verify typecheck and lint**

Run: `cd web && npm run typecheck && npm run lint`
Expected: both exit 0.

- [ ] **Step 10.7: Commit**

```bash
git add web/ && git commit -m "$(cat <<'EOF'
feat(web/p1): add AppShell + Header + Footer + MobileNav

- Header sticky with brand, nav skeleton, user menu (login/signup or signout)
- Footer with legal links (placeholder routes for now)
- MobileNav bottom tabs hidden on md+
- AppShell composes Header + main + Footer + MobileNav

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11 — Auth pages (Signup, Login, Callback)

**Files:**
- Create: `web/src/pages/auth/SignupPage.tsx`
- Create: `web/src/pages/auth/LoginPage.tsx`
- Create: `web/src/pages/auth/CallbackPage.tsx`
- Create: `web/src/pages/HomePage.tsx`
- Create: `web/src/pages/account/AccountPage.tsx`
- Create: `web/src/pages/NotFoundPage.tsx`

- [ ] **Step 11.1: Write `web/src/pages/auth/SignupPage.tsx`**

```tsx
import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function SignupPage() {
  const { signUp, signInWithGoogle } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get('next') ?? '/account';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    setSubmitting(true);
    const { error } = await signUp(email, password);
    setSubmitting(false);
    if (error) {
      setError(error.message);
      return;
    }
    setInfo("Compte créé. Vérifie tes emails pour confirmer ton adresse, puis connecte-toi.");
    setTimeout(() => navigate(`/auth/login?next=${encodeURIComponent(next)}`), 2000);
  }

  async function onGoogle() {
    setError(null);
    const redirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(next)}`;
    const { error } = await signInWithGoogle(redirectTo);
    if (error) setError(error.message);
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 bg-background">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold">Créer un compte</h1>
          <p className="text-sm text-muted-foreground">Gratuit. Aucune carte bancaire requise.</p>
        </div>

        <Button variant="outline" className="w-full" onClick={() => void onGoogle()}>
          Continuer avec Google
        </Button>

        <div className="relative">
          <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-border" /></div>
          <div className="relative flex justify-center text-xs uppercase"><span className="bg-background px-2 text-muted-foreground">ou</span></div>
        </div>

        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Mot de passe</Label>
            <Input id="password" type="password" required minLength={8} autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          {error && <p role="alert" className="text-sm text-danger">{error}</p>}
          {info && <p role="status" className="text-sm text-success">{info}</p>}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Création…' : "S'inscrire"}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          Déjà un compte ?{' '}
          <Link to={`/auth/login?next=${encodeURIComponent(next)}`} className="text-primary hover:underline">
            Se connecter
          </Link>
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 11.2: Write `web/src/pages/auth/LoginPage.tsx`**

```tsx
import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function LoginPage() {
  const { signIn, signInWithGoogle } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get('next') ?? '/account';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    const { error } = await signIn(email, password);
    setSubmitting(false);
    if (error) {
      setError(error.message);
      return;
    }
    navigate(next, { replace: true });
  }

  async function onGoogle() {
    setError(null);
    const redirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(next)}`;
    const { error } = await signInWithGoogle(redirectTo);
    if (error) setError(error.message);
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 bg-background">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold">Connexion</h1>
        </div>

        <Button variant="outline" className="w-full" onClick={() => void onGoogle()}>
          Continuer avec Google
        </Button>

        <div className="relative">
          <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-border" /></div>
          <div className="relative flex justify-center text-xs uppercase"><span className="bg-background px-2 text-muted-foreground">ou</span></div>
        </div>

        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Mot de passe</Label>
            <Input id="password" type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          {error && <p role="alert" className="text-sm text-danger">{error}</p>}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Connexion…' : 'Se connecter'}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          Pas encore de compte ?{' '}
          <Link to={`/auth/signup?next=${encodeURIComponent(next)}`} className="text-primary hover:underline">
            S'inscrire
          </Link>
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 11.3: Write `web/src/pages/auth/CallbackPage.tsx`**

```tsx
import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { FullPageSpinner } from '@/components/shared/LoadingSpinner';

export default function CallbackPage() {
  const { loading, user } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();

  useEffect(() => {
    if (loading) return;
    const next = params.get('next') ?? '/account';
    navigate(user ? next : '/auth/login', { replace: true });
  }, [loading, user, navigate, params]);

  return <FullPageSpinner />;
}
```

- [ ] **Step 11.4: Write `web/src/pages/HomePage.tsx`**

```tsx
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';

export default function HomePage() {
  const { user } = useAuth();
  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-16">
      <div className="space-y-6 text-center">
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
          Probabilités sportives, calculées par IA.
        </h1>
        <p className="text-lg text-muted-foreground">
          Foot et NHL. 8 ligues. Probas par marché, picks du jour, performance vérifiable.
        </p>
        <div className="flex justify-center gap-3">
          {user ? (
            <Button asChild size="lg"><Link to="/account">Mon compte</Link></Button>
          ) : (
            <>
              <Button asChild size="lg"><Link to="/auth/signup">Créer un compte gratuit</Link></Button>
              <Button asChild size="lg" variant="outline"><Link to="/auth/login">Se connecter</Link></Button>
            </>
          )}
        </div>
        <p className="text-xs text-muted-foreground pt-8">
          V2 en construction · Foundation P1 — pages métier livrées en P2.
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 11.5: Write `web/src/pages/account/AccountPage.tsx`**

```tsx
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';

export default function AccountPage() {
  const { user, signOut } = useAuth();
  return (
    <div className="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8 py-12 space-y-6">
      <h1 className="text-2xl font-bold">Mon compte</h1>
      <div className="rounded-lg border border-border bg-card p-6 space-y-2">
        <div className="text-sm text-muted-foreground">Email connecté</div>
        <div className="text-base">{user?.email}</div>
      </div>
      <Button variant="outline" onClick={() => void signOut()}>Se déconnecter</Button>
    </div>
  );
}
```

- [ ] **Step 11.6: Write `web/src/pages/NotFoundPage.tsx`**

```tsx
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

export default function NotFoundPage() {
  return (
    <div className="mx-auto max-w-md px-6 py-24 text-center space-y-4">
      <h1 className="text-3xl font-bold">404</h1>
      <p className="text-muted-foreground">Cette page n'existe pas.</p>
      <Button asChild><Link to="/">Retour à l'accueil</Link></Button>
    </div>
  );
}
```

- [ ] **Step 11.7: Verify typecheck and lint**

Run: `cd web && npm run typecheck && npm run lint`
Expected: both exit 0.

- [ ] **Step 11.8: Commit**

```bash
git add web/ && git commit -m "$(cat <<'EOF'
feat(web/p1): add auth pages (Signup, Login, Callback) + Home + Account + 404

- Signup: email/password + Google OAuth, redirect to /auth/login after confirm
- Login: email/password + Google OAuth, redirect to ?next= or /account
- Callback: handles OAuth return, redirects based on session state
- HomePage: minimal landing with CTAs (real V2 home in P2)
- AccountPage: shows email + signout (placeholder, expanded in P3)
- NotFoundPage: 404

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12 — Wire router + providers in App.tsx

**Files:**
- Create: `web/src/routes.tsx`
- Modify: `web/src/App.tsx`

- [ ] **Step 12.1: Write `web/src/routes.tsx`**

```tsx
import { Routes, Route } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { ProtectedRoute } from '@/components/shared/ProtectedRoute';
import HomePage from '@/pages/HomePage';
import SignupPage from '@/pages/auth/SignupPage';
import LoginPage from '@/pages/auth/LoginPage';
import CallbackPage from '@/pages/auth/CallbackPage';
import AccountPage from '@/pages/account/AccountPage';
import NotFoundPage from '@/pages/NotFoundPage';

export function AppRoutes() {
  return (
    <Routes>
      {/* Auth pages — no shell (full-screen layout) */}
      <Route path="/auth/signup" element={<SignupPage />} />
      <Route path="/auth/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<CallbackPage />} />

      {/* All other pages — shell wrapped */}
      <Route path="/" element={<AppShell><HomePage /></AppShell>} />
      <Route
        path="/account"
        element={
          <AppShell>
            <ProtectedRoute>
              <AccountPage />
            </ProtectedRoute>
          </AppShell>
        }
      />
      <Route path="*" element={<AppShell><NotFoundPage /></AppShell>} />
    </Routes>
  );
}
```

- [ ] **Step 12.2: Replace `web/src/App.tsx`**

```tsx
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { AppRoutes } from '@/routes';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
```

- [ ] **Step 12.3: Verify dev server boots and routes work**

Run: `cd web && npm run dev` and open http://localhost:5173.
Expected:
1. `/` shows HomePage with CTAs
2. `/auth/signup` shows signup form (no shell)
3. `/auth/login` shows login form (no shell)
4. `/account` redirects to `/auth/login?next=%2Faccount` (no session)
5. `/anything-else` shows 404 inside shell
Stop with Ctrl+C.

- [ ] **Step 12.4: Verify typecheck, lint, tests**

Run: `cd web && npm run typecheck && npm run lint && npm run test:ci`
Expected: all green.

- [ ] **Step 12.5: Commit**

```bash
git add web/ && git commit -m "$(cat <<'EOF'
feat(web/p1): wire router + providers in App.tsx

- routes.tsx is the single route table source of truth
- Auth pages render without shell (full-screen)
- Other pages wrapped in AppShell
- /account uses ProtectedRoute → /auth/login?next=...
- Top-level: ErrorBoundary > QueryClient > BrowserRouter > AuthProvider

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13 — Playwright E2E tests for auth happy path

**Files:**
- Create: `web/playwright.config.ts`
- Create: `web/e2e/helpers/test-user.ts`
- Create: `web/e2e/auth-signup.spec.ts`
- Create: `web/e2e/auth-login-logout.spec.ts`
- Modify: `web/.env.example` (add SUPABASE_SERVICE_ROLE_KEY for tests)
- Modify: `web/package.json` (add `@supabase/supabase-js` already present, ensure)

**Important:** these E2E tests require a `SUPABASE_SERVICE_ROLE_KEY` to create and delete test users. This key is **NEVER** committed. It's set as an environment variable locally and as a CI secret.

- [ ] **Step 13.1: Update `web/.env.example`**

```bash
cat > web/.env.example <<'EOF'
# Supabase (frontend public credentials — anon key only)
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOi...

# Backend FastAPI URL
VITE_API_URL=http://localhost:8000

# E2E ONLY — server-side service role for creating/deleting test users
# NEVER set this in production. Required only when running `npm run e2e`.
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...
EOF
```

- [ ] **Step 13.2: Write `web/playwright.config.ts`**

```ts
import { defineConfig, devices } from '@playwright/test';

const PORT = 4173;
const baseURL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'npm run build && npm run preview -- --port 4173',
    port: PORT,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
```

- [ ] **Step 13.3: Write `web/e2e/helpers/test-user.ts`**

```ts
import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const URL = process.env.VITE_SUPABASE_URL ?? '';
const SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY ?? '';

if (!URL || !SERVICE_KEY) {
  throw new Error(
    'E2E requires VITE_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY env vars set in your shell.'
  );
}

const admin: SupabaseClient = createClient(URL, SERVICE_KEY, {
  auth: { autoRefreshToken: false, persistSession: false },
});

export interface TestUser {
  id: string;
  email: string;
  password: string;
}

export async function createTestUser(): Promise<TestUser> {
  const id = crypto.randomUUID();
  const email = `e2e-${id}@probalab-test.local`;
  const password = `Test-${id}-!`;

  const { data, error } = await admin.auth.admin.createUser({
    email,
    password,
    email_confirm: true,
  });
  if (error || !data.user) throw error ?? new Error('createUser returned no user');

  return { id: data.user.id, email, password };
}

export async function deleteTestUser(userId: string): Promise<void> {
  const { error } = await admin.auth.admin.deleteUser(userId);
  if (error) console.warn(`Failed to delete test user ${userId}:`, error.message);
}
```

- [ ] **Step 13.4: Write `web/e2e/auth-signup.spec.ts`**

```ts
import { test, expect } from '@playwright/test';
import { deleteTestUser } from './helpers/test-user';

test.describe('Signup flow', () => {
  let createdUserId: string | null = null;

  test.afterEach(async () => {
    if (createdUserId) {
      await deleteTestUser(createdUserId);
      createdUserId = null;
    }
  });

  test('user can submit signup form and gets the confirmation message', async ({ page }) => {
    const id = crypto.randomUUID();
    const email = `e2e-${id}@probalab-test.local`;
    const password = `Test-${id}-!`;

    await page.goto('/auth/signup');
    await expect(page.getByRole('heading', { name: /créer un compte/i })).toBeVisible();

    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/mot de passe/i).fill(password);
    await page.getByRole('button', { name: /s'inscrire/i }).click();

    // Wait for confirmation status message
    await expect(page.getByRole('status')).toContainText(/vérifie tes emails/i, { timeout: 10_000 });

    // Cleanup: lookup user id via admin API. Email is unique enough — fetch by email.
    const { createClient } = await import('@supabase/supabase-js');
    const admin = createClient(
      process.env.VITE_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!,
      { auth: { autoRefreshToken: false, persistSession: false } }
    );
    const { data } = await admin.auth.admin.listUsers();
    const u = data.users.find((u) => u.email === email);
    if (u) createdUserId = u.id;
  });
});
```

- [ ] **Step 13.5: Write `web/e2e/auth-login-logout.spec.ts`**

```ts
import { test, expect } from '@playwright/test';
import { createTestUser, deleteTestUser, type TestUser } from './helpers/test-user';

test.describe('Login + logout flow', () => {
  let user: TestUser;

  test.beforeAll(async () => {
    user = await createTestUser();
  });

  test.afterAll(async () => {
    await deleteTestUser(user.id);
  });

  test('user can login with email/password, sees account, logs out', async ({ page }) => {
    await page.goto('/auth/login');
    await page.getByLabel(/email/i).fill(user.email);
    await page.getByLabel(/mot de passe/i).fill(user.password);
    await page.getByRole('button', { name: /se connecter/i }).click();

    await expect(page).toHaveURL(/\/account$/, { timeout: 10_000 });
    await expect(page.getByRole('heading', { name: /mon compte/i })).toBeVisible();
    await expect(page.getByText(user.email)).toBeVisible();

    await page.getByRole('button', { name: /se déconnecter/i }).click();

    // After logout, header shows the Connexion/Inscription buttons again on home
    await expect(page).toHaveURL('/', { timeout: 5_000 });
    await expect(page.getByRole('link', { name: /^connexion$/i })).toBeVisible();
  });

  test('protected route redirects unauthenticated user to login', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/account');
    await expect(page).toHaveURL(/\/auth\/login\?next=%2Faccount/, { timeout: 5_000 });
  });
});
```

**Note on signOut + redirect:** `signOut` from `useAuth` doesn't navigate — Header just changes state. The test goes back to `/` because the AccountPage will re-render with no user, and `<ProtectedRoute>` will redirect. Adjust if behavior differs in practice.

Actually looking again, the test above expects `/` after logout, but the actual behavior with `<ProtectedRoute>` is that the page navigates to `/auth/login?next=%2Faccount`. Adjust:

- [ ] **Step 13.6: Adjust the logout assertion in `web/e2e/auth-login-logout.spec.ts`**

Replace the assertion `await expect(page).toHaveURL('/', ...)` with:

```ts
await expect(page).toHaveURL(/\/auth\/login/, { timeout: 5_000 });
await expect(page.getByRole('heading', { name: /connexion/i })).toBeVisible();
```

The full block becomes:

```ts
    await page.getByRole('button', { name: /se déconnecter/i }).click();

    // After logout on /account, ProtectedRoute kicks back to /auth/login
    await expect(page).toHaveURL(/\/auth\/login/, { timeout: 5_000 });
    await expect(page.getByRole('heading', { name: /connexion/i })).toBeVisible();
```

- [ ] **Step 13.7: Install Playwright browsers**

Run: `cd web && npx playwright install --with-deps chromium`
Expected: Chromium downloaded.

- [ ] **Step 13.8: Run E2E tests locally**

Prerequisites:
1. `web/.env.local` is filled with real `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.
2. `SUPABASE_SERVICE_ROLE_KEY` is exported in your shell (NOT in `.env.local` — Playwright reads from process env). Get it from Supabase Studio → Project Settings → API.

```bash
export VITE_SUPABASE_URL="https://yskpqdnidxojoclmqcxn.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="eyJ...service-role..."
cd web && npm run e2e
```

Expected: 3 E2E tests pass (signup, login+logout, protected route redirect).

If signup test fails because the Supabase project enforces email confirmation strictly, the user IS created (waiting for confirm) and the cleanup still works via `admin.deleteUser`. The test only asserts the confirmation message in the UI, which is correct behavior.

- [ ] **Step 13.9: Commit**

```bash
git add web/ && git commit -m "$(cat <<'EOF'
test(web/p1): add Playwright E2E for signup, login, logout, protected route

- helpers/test-user.ts uses Supabase admin API to create/delete test users
- auth-signup.spec.ts: form submission shows confirmation message
- auth-login-logout.spec.ts: full login → account → logout flow
- Protected route test: anonymous /account redirects to /auth/login?next=...
- SUPABASE_SERVICE_ROLE_KEY required only for E2E (documented in .env.example)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 14 — Vercel deployment config + README

**Files:**
- Create: `web/vercel.json`
- Create: `web/README.md`
- Create: `web/public/robots.txt`

- [ ] **Step 14.1: Write `web/vercel.json`**

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install",
  "framework": "vite",
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

- [ ] **Step 14.2: Write `web/public/robots.txt`** (placeholder — final SEO version comes in P6)

```
# P1 placeholder. Disallow indexing during construction.
# Final robots.txt + sitemap routing comes in P6.
User-agent: *
Disallow: /
```

- [ ] **Step 14.3: Write `web/README.md`**

````markdown
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

## Architecture

See `docs/superpowers/specs/2026-05-06-probalab-v2-relaunch-design.md`.

P1 (this commit batch) covers : skeleton + design tokens + auth shell. Pages métier come in P2.

## Project structure

```
src/
├── lib/                  # Supabase client, API fetcher, utils
├── contexts/             # AuthContext (session state)
├── hooks/                # useAuth + future useMatch, usePicks, etc.
├── components/
│   ├── ui/               # shadcn primitives (button, input, dialog, …)
│   ├── layout/           # Shell (Header, Footer, MobileNav)
│   └── shared/           # ErrorBoundary, ProtectedRoute, Spinners
├── pages/                # Route-level components
├── styles/               # globals.css + tokens.css
├── types/                # env types
└── routes.tsx            # Route table
```

## Deployment

Vercel project name: `probalab-web`. SPA rewrite via `vercel.json`. Preview only in P1 (no DNS switch yet).
````

- [ ] **Step 14.4: Verify build for production succeeds**

Run: `cd web && npm run build`
Expected: `dist/index.html` and `dist/assets/*.js`+`*.css` present, no errors.

- [ ] **Step 14.5: Commit**

```bash
git add web/ && git commit -m "$(cat <<'EOF'
chore(web/p1): add vercel.json + robots.txt placeholder + README

- vercel.json: SPA rewrites all paths → /index.html
- robots.txt: disallow all (final version comes in P6 with sitemaps)
- README documents quick start, scripts, structure, deployment notes

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 15 — CI workflow (optional but recommended)

**Files:**
- Modify or create: `.github/workflows/web-ci.yml`

This is optional and may need adjustment based on existing CI in `.github/workflows/`. Check first :

- [ ] **Step 15.1: Inspect existing CI workflows**

```bash
ls .github/workflows/
```

If a workflow already runs the `dashboard/`, copy its structure for `web/` (or skip this task and add CI in P2 once we have more to test).

- [ ] **Step 15.2 (conditional): Create `.github/workflows/web-ci.yml`**

If no CI exists for `web/`, write:

```yaml
name: web-ci
on:
  push:
    paths: ['web/**', '.github/workflows/web-ci.yml']
  pull_request:
    paths: ['web/**']

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: web
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
          cache-dependency-path: web/package-lock.json
      - run: npm ci
      - run: npm run typecheck
      - run: npm run lint
      - run: npm run test:ci
      - run: npm run build
```

- [ ] **Step 15.3 (conditional): Commit**

```bash
git add .github/workflows/web-ci.yml && git commit -m "$(cat <<'EOF'
ci(web/p1): typecheck + lint + unit tests + build on push

E2E tests excluded from CI for now (require SUPABASE_SERVICE_ROLE_KEY
secret — to be added in P3 when conversion testing matters).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 16 — Final verification + push

- [ ] **Step 16.1: Run the full local check sequence**

```bash
cd web
npm run typecheck
npm run lint
npm run test:ci
npm run build
```

Expected: all 4 commands exit 0.

- [ ] **Step 16.2: Verify the dev experience end-to-end manually**

```bash
npm run dev
```

Open http://localhost:5173 and walk through:
1. Home renders with brand and CTAs.
2. Click "Créer un compte" → signup form, no shell.
3. Click "Continuer avec Google" → redirected to Google (cancel and come back).
4. Click "Se connecter" link → login form.
5. Fill bogus credentials, submit → see error message.
6. Manually navigate to `/account` → redirected to `/auth/login?next=%2Faccount`.
7. Header on home shows "Connexion" / "Inscription" buttons.
8. Resize to mobile → MobileNav appears at bottom.
9. Navigate to `/anything-else` → 404 inside shell.

Stop with Ctrl+C.

- [ ] **Step 16.3: Push branch**

```bash
git push -u origin claude/busy-blackburn-0ee195
```

- [ ] **Step 16.4: Optional — create draft PR**

```bash
gh pr create --draft --title "feat(web/p1): foundation — Vite skeleton + auth shell" --body "$(cat <<'EOF'
## Summary

P1 of the V2 relaunch. Greenfield `web/` SPA built in parallel with the existing `ProbaLab/dashboard/`.

- Vite 7 + React 19 + TS strict + Tailwind 4 + shadcn primitives
- Supabase auth (email/password + Google OAuth) with AuthContext
- ErrorBoundary at root + ProtectedRoute guard
- Layout shell (Header, Footer, MobileNav)
- Auth pages: Signup, Login, Callback + placeholder Home, Account, 404
- Vitest unit tests (15 passing) + Playwright E2E (3 happy paths)
- Vercel SPA config

Spec: [docs/superpowers/specs/2026-05-06-probalab-v2-relaunch-design.md](../blob/main/docs/superpowers/specs/2026-05-06-probalab-v2-relaunch-design.md)
Plan: [docs/superpowers/plans/2026-05-06-p1-foundation.md](../blob/main/docs/superpowers/plans/2026-05-06-p1-foundation.md)

P2 (pages publiques métier) follows.

## Test plan

- [ ] `cd web && npm install && npm run typecheck && npm run lint && npm run test:ci && npm run build` all pass
- [ ] `npm run dev` boots, manual walk-through (steps in plan task 16.2) works
- [ ] `npm run e2e` passes (requires SUPABASE_SERVICE_ROLE_KEY env var)
- [ ] No regression on existing `ProbaLab/dashboard/` (untouched)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Definition of Done for P1

- [ ] All 16 tasks above checked
- [ ] `cd web && npm run typecheck && npm run lint && npm run test:ci && npm run build` exits 0
- [ ] `cd web && npm run e2e` passes locally with valid env vars
- [ ] Manual walk-through (Task 16.2) works end-to-end
- [ ] No file in `ProbaLab/dashboard/` was modified by P1
- [ ] No new env var added to backend `ProbaLab/` (only frontend `web/` env vars)
- [ ] Branch `claude/busy-blackburn-0ee195` pushed
- [ ] Optional: draft PR opened

---

*Plan complet pour P1. Next sub-plan : P2 — pages publiques métier (home avec données réelles, page match free, page picks free, page performance niveaux 1+2). Sera rédigé une fois P1 mergé.*
