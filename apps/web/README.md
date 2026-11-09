# CheapWings web

React + TypeScript + Vite client for the FastAPI backend. Follow the repository
[root README](../../README.md) for API/worker startup and live-provider configuration.

From this directory, with Node 22.18+ (the project currently uses Node 26):

```sh
npm ci
cp .env.example .env
npm run dev -- --host localhost --port 5173 --strictPort
```

Open `http://localhost:5173`. Keep the backend API and worker running in separate
terminals. `VITE_API_BASE_URL` selects the backend; localhost access needs no token.
For a private authenticated backend, expand **Private server access** and enter the
owner token at runtime. It stays in tab memory and must be entered again after a
refresh. Never put a bearer token or upstream credential in a `VITE_*` variable.

```sh
npm test
npm run build
# Browser regressions; install Chromium once if it is absent:
npx playwright install chromium
npm run test:browser
```

The browser suite serves the built bundle and synthetic API responses through
Playwright request interception, without contacting a provider or starting a web
server. It covers empty safe results switching to advertised results, cursor
pagination, refresh/recovery, runtime auth, expiry, and cancellation with retained
fares. The suite now includes the four core flows and 36 P4.5 state/viewport checks at
375/768/1440px. All passed during integration. In a restricted sandbox,
Chromium may need additional execution permission. Integrated synthetic screenshots are retained in `../../docs/design/p45-qa/`.
See WORK_LOG.md for exact validation evidence and current runtime configuration.

Public API types are maintained in `src/api/types.ts` against
`../../contracts/openapi.yaml`. Money stays as decimal strings. The backend owns
ranking, currency conversion, coverage, provider calls, and durable execution.
