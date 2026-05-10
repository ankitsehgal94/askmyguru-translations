# Translation API — Wire Format Reference

This folder contains canonical sample responses backend should mirror exactly.

## URLs (live, served by GitHub Pages)

- English: <https://ankitsehgal94.github.io/askmyguru-translations/samples/sample-en-IN.json>
- Hindi: <https://ankitsehgal94.github.io/askmyguru-translations/samples/sample-hi-IN.json>

These mirror the production endpoint files at `/translations/<lang>.json` but
are pinned references for backend implementation. They will not change without
a coordinated bump.

## Contract

### Endpoint shape

```
GET /v1/translations/:lang
```

`:lang` is a BCP 47 tag — `en-IN`, `hi-IN`, `ta-IN`, `te-IN`, `kn-IN`,
`mr-IN`, `bn-IN`. Path param, not query, so a CDN can cache by URL.

### Response body

```json
{
  "hashValue": "<sha256 of the translation object's content>",
  "translation": {
    "<namespace>.<key.path>": "<translated value>",
    "<namespace>.<key.path>.<sub-key>": "<translated value>",
    "<namespace>.<key.path>": [...array of translated values...],
    ...
  }
}
```

**Key points:**

- Top-level field name is `translation` (singular). Not `translations`.
- All keys are flat dotted strings with the namespace as the first segment.
- The frontend supports 18 namespaces today: `common`, `auth`, `onboarding`,
  `home`, `chat`, `wallet`, `reports`, `marketing`, `profile`, `dasha`,
  `relationships`, `categories`, `navigation`, `notifications`, `support`,
  `shopping`, `vedshala`, `match-making`. Backend can ship a partial set;
  missing namespaces fall back to bundled English on the client.
- Arrays remain native JSON arrays at their key. Do **not** decompose into
  `<key>.0`, `<key>.1` — see "Arrays" below.

### Required HTTP headers

| Header          | Value                                  | Why                                                             |
| --------------- | -------------------------------------- | --------------------------------------------------------------- |
| `Content-Type`  | `application/json; charset=utf-8`      | Devanagari and other non-ASCII scripts render correctly         |
| `ETag`          | `"<hashValue>"`                        | Enables `If-None-Match` round-trip → 304 Not Modified responses |
| `Cache-Control` | `public, no-cache, must-revalidate`    | Forces revalidation each launch but allows 304                  |
| `Vary`          | `Accept-Encoding`                      | Lets CDN serve correct gzip vs identity per client              |

### Recommended HTTP headers

| Header             | Value             | Why                                          |
| ------------------ | ----------------- | -------------------------------------------- |
| `Content-Encoding` | `gzip` or `br`    | Cuts payload by ~70%                         |
| `Last-Modified`    | RFC 7231 date     | Optional alternative to ETag                 |

### Conditional requests (304)

```
GET /v1/translations/hi-IN
If-None-Match: "abc123..."

→ HTTP/1.1 304 Not Modified
  ETag: "abc123..."
```

Empty body. Saves bandwidth on cache hits — already wired up in client.

### 404 for unsupported language

```json
{
  "error": "language_not_supported",
  "supportedLanguages": ["en-IN", "hi-IN", "ta-IN", "te-IN", "kn-IN", "mr-IN", "bn-IN"]
}
```

Client falls back to `en-IN` automatically.

## Interpolation

Backend ships placeholders verbatim using i18next's `{{var}}` syntax:

```json
"chat.guruPricing.priceLabel": "₹{{price}}/{{count}} Chats",
"chat.guruPricing.paidChatPriceText": "₹{{cost}}/{{count}} chats"
```

Frontend supplies the values at call-site:

```ts
t('guruPricing.priceLabel', { price: 84, count: 10 })  // → "₹84/10 Chats"
```

Do not pre-substitute on backend.

## Plurals

i18next plural keys end with `_one`, `_other`:

```json
"chat.guruPricing.freeChatsCount_one": "1 Free Chat",
"chat.guruPricing.freeChatsCount_other": "{{count}} Free Chats"
```

Frontend calls `t('guruPricing.freeChatsCount', { count: N })`. i18next
picks the correct variant. Hindi uses the same `_one` / `_other` rules
as English (count !== 1 → other).

## Arrays

Arrays remain **native JSON arrays at their key**:

```json
"profile.deleteAccount.consequences": [
  "Your profile details and all secondary profiles will be permanently deleted",
  "Your Guru Coin balance will be reset to 0.",
  "Your chat history will be deleted.",
  "Your downloaded reports, if any, will be deleted.",
  "Any chat packs, offers, etc...",
  "All Profile linked to the profile will be deleted",
  "Any active subscriptions will be cancelled..."
]
```

**Do NOT** ship as:

```json
// ❌ Wrong — decomposed into per-element keys
"profile.deleteAccount.consequences.0": "Your profile details...",
"profile.deleteAccount.consequences.1": "Your Guru Coin balance..."
```

The frontend uses `t(key, { returnObjects: true })` to get the array back as
a real `Array<T>` for `.map()` / `.filter()`. Decomposed format breaks this.

For arrays of objects (e.g. FAQ items), nest the objects inside the array:

```json
"chat.freeChatFaq.faqItems": [
  { "question": "What do you get?", "answer": "You get 2 Free Chats..." },
  { "question": "How many days?",   "answer": "7 days..." }
]
```

## Nested objects (rare)

If a key's value is an object (rare in our usage but supported), it stays
nested in the JSON value:

```json
"some.config.values": {
  "primary": "Primary value",
  "secondary": "Secondary value"
}
```

Frontend's `t('some.config.values', { returnObjects: true })` returns the
whole object.

## What to NOT do

- ❌ `translations` (plural) instead of `translation` (singular)
- ❌ Nested namespace at the top level instead of flat
- ❌ Decompose arrays into numeric-suffix keys
- ❌ Pre-substitute `{{var}}` placeholders
- ❌ Authenticate this endpoint (translations are public)
- ❌ Serve different content based on auth headers (Vary: Authorization)
- ❌ Strip the `-IN` region tag from the language code

## Mobile client storage

Client caches each language locally in AsyncStorage along with the ETag.
On subsequent launches the client sends `If-None-Match` with the saved
ETag and expects 304 if content is unchanged. So the value of the ETag
header **must be stable** for stable content (deterministic hash, not a
fresh timestamp on every request).

## Performance targets

- Response size (gzipped, full bundle): **~30-60 KB**
- Backend p95 TTFB from origin: **< 100 ms**
- Origin compute: **< 20 ms** (the response should be cacheable, not
  generated per-request)

## Implementation suggestion

Backend can store keys flat in their database (`(language, key, value)`
rows) — that's a great fit for translator-team workflows. The
serialization step into the API response should:

1. Filter by `language`
2. Group rows back into the flat `{ "key": "value" }` object
3. Compute `hashValue = sha256(JSON.stringify(translationObject))`
4. Cache the result in Redis keyed by `lang` (invalidate on row writes)
5. Set `ETag: "<hashValue>"` and serve

Total backend transform: ~10 lines in any language.

## Versioning

We won't pin to a specific `hashValue` from the client side — clients send
the *previous* response's hash and rely on backend's ETag comparison.
Backend doesn't need to track versions explicitly; the content hash IS
the version.
