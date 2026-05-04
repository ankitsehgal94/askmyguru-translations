# askmyguru-translations

Translation JSONs for the [AskMyGuru](https://askmyguru.live) mobile app, served via GitHub Pages.

This repo hosts the translation source-of-truth while the backend `/v1/translations` endpoint is being built. The mobile app's `i18next-http-backend` fetches from these URLs at runtime, with AsyncStorage caching and a bundled English fallback.

## URLs

- English: https://ankitsehgal94.github.io/askmyguru-translations/translations/en-IN.json
- Hindi:   https://ankitsehgal94.github.io/askmyguru-translations/translations/hi-IN.json

## Shape

Each file follows the contract documented in the mobile app at `docs/backend-translations-endpoint-contract.md`:

```json
{
  "version": "2026-05-04-v1",
  "lang": "en-IN",
  "translations": {
    "common":     { "...": "..." },
    "auth":       { "...": "..." },
    "onboarding": { "...": "..." },
    "...": "...",
    "match-making": { "...": "..." }
  }
}
```

All 18 namespaces are present in every language file. Phase 1 populates `common`, `auth`, `onboarding`. Other namespaces are `{}` until their phase ships.

## Editing translations

1. Edit `translations/{lang}.json` directly
2. Bump the `version` field (any monotonically newer string)
3. Commit + push to `main`
4. GitHub Pages publishes the change automatically (~1 min propagation)
5. App users see the new copy on next cold start (or when AsyncStorage cache misses)

**No app release required.**

## Migration to real backend

When the backend `/v1/translations` endpoint goes live, the mobile app changes one URL constant in `services/i18n/index.ts` to point at the new API. This repo can either be archived or kept as a fallback host.
