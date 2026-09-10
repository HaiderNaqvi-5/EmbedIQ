# EmbedIQ frontend

The frontend is a Next.js application containing the authenticated dashboard,
bot and knowledge-base management screens, analytics, branding settings, and
the public chat widget.

## Routes

- `/`: product landing page
- `/login` and `/register`: authentication screens
- `/dashboard`: bot and knowledge-base dashboard
- `/widget/chat`: standalone widget preview
- `/widget/test`: widget testing page

The embeddable browser script is published from
`frontend/public/widget.js`. The dashboard uses the API helpers in
`frontend/lib/api.ts` and authentication helpers in `frontend/lib/auth.ts`.

## Local development

Install dependencies and start the development server:

```bash
cd frontend
npm ci
npm run dev
```

The app runs at `http://localhost:3000`. Configure the API origin using the
frontend environment variables described in `.env.example`; keep local
overrides in `.env.local`, which is ignored by Git.

## Validation

```bash
npm run build
npm run lint
```

The frontend uses Next.js 14, React 18, TypeScript, Tailwind CSS, and
`react-markdown` for rendered chat responses.
