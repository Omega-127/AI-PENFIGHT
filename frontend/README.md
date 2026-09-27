# Frontend — AI Penfight

Next.js + TypeScript + Tailwind, per ARCHITECTURE.md §2 and §4.

## Setup

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

## Structure

- `app/` — routes: `/` (Home), `/analysis`, `/history`, `/dashboard`
- `components/layout/` — Nav, Footer
- `components/input/` — MarkupDemo (the interactive live-annotation demo)
- `components/analysis/` — HowItWorks, Capabilities
- `components/feedback/` — MarkList (renders findings)
- `components/dashboard/` — ProgressChart, ProgressSection
- `lib/api.ts` — single typed API client (matches ARCHITECTURE.md §4 contract)
- `lib/types.ts`, `lib/constants.ts`

`components/input/MarkupDemo.tsx` currently runs a local heuristic
(`lib/markup-heuristics.ts`) instead of calling the backend, so the
demo works with no API running. Swap it for `lib/api.ts`'s `analyze()`
once `POST /api/v1/analyze` exists.
