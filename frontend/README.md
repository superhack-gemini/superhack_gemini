# Gemini Sports Narrative Studio

A cinematic, hackathon-ready frontend that simulates generating a Gemini-style sports narrative video from a prompt. The backend is mocked locally but structured so it can be swapped with a real API later.

## Local Development

```bash
npm install
npm run dev
```

Vite will output the local URL. The app is ready for Vercel or Netlify deployment.

## Project Structure

- `src/App.tsx` — main UI flow (input, generation, hero output)
- `src/services/narrativeService.ts` — mocked API call
- `src/index.css` — Tailwind + global styles

## Swapping In a Real Backend

Replace the mocked implementation in `src/services/narrativeService.ts`:

- Keep the `generateNarrative(prompt: string): Promise<VideoResult>` signature
- Replace the `wait(...)` call with a real `fetch` / API client
- Return the real `VideoResult` from your API

The UI depends only on this service and does not know that it is mocked.

## Deploying to Vercel

From the project root (`frontend/`):

```bash
vercel
```

Production deploy:

```bash
vercel --prod
```

After changes, redeploy by re-running `vercel --prod` from the same directory.
