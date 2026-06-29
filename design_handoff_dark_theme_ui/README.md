# Handoff: Selectarr Dark-Theme UI Redesign

## Overview

Selectarr is a manual media-management tool that integrates **Jellyfin**, **Radarr**, **Sonarr**, and **Lidarr**. Users browse their library filtered by watch status and selectively delete media at any level of granularity — with a mandatory confirmation step and optional dry-run mode.

This handoff covers a dark-theme redesign of the entire web UI. It replaces the current Pico CSS default styling with a dense, technical, *arr-style dark theme tailored to homelab users. All five existing pages (Movies, Series, Music, Activity / Logs, Settings) are covered, plus the deletion confirm/result flow.

## About the Design Files

The files in this bundle are **design references created in HTML/React** — a working prototype showing the intended look and behaviour. They are **not production code to ship directly**.

The Selectarr codebase uses **FastAPI + Jinja2 templates + HTMX** (see `selectarr/app/templates/`). The task is to recreate the visual design in that existing stack:

- Port the styling (CSS variables + class names) into a new stylesheet that replaces or augments the current inline `<style>` block in `base.html`.
- Update the Jinja2 templates and HTMX partials to use the new class names and component structure.
- **Keep HTMX as the interaction layer** — the React in the prototype only exists to make the design clickable. Every state in the prototype (filter changes, expand rows, confirm panel, delete result) maps to an existing HTMX endpoint in `app/routers/`.
- The drawer-style confirm panel can be implemented with HTMX targeting a fixed-position container — no JS framework required.

If a different framework is later chosen, treat the prototype as a visual spec, not as the implementation.

## Fidelity

**High-fidelity (hifi).** Final colors, typography, spacing, borders, and interaction states are all specified. Reproduce pixel-perfectly using the existing Jinja/HTMX stack.

## Design Tokens

All tokens are defined as CSS custom properties in `styles.css` under `:root`. Below is the canonical list — port these to a CSS file (e.g. `app/static/css/selectarr.css`) and serve it from FastAPI's static mount.

### Colors — surfaces

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0d1015` | Page background |
| `--bg-elevated` | `#11151c` | Table headers, drawer body, inputs |
| `--surface` | `#161b25` | Cards, filter bars, table card |
| `--surface-2` | `#1c2230` | Row hover, secondary buttons |
| `--surface-3` | `#232a3a` | Hover on secondary surfaces, toggle track |
| `--border` | `#232938` | Standard borders |
| `--border-strong` | `#2e3548` | Inputs, strong dividers |
| `--border-subtle` | `rgba(255,255,255,0.04)` | Table row dividers |

### Colors — text

| Token | Value | Use |
|---|---|---|
| `--text` | `#e5e8ee` | Body text |
| `--text-strong` | `#f3f5f9` | Headings, titles |
| `--text-muted` | `#8a92a3` | Subtitles, hints, meta |
| `--text-dim` | `#5a6276` | Disabled, placeholders, table-header labels |

### Colors — brand & status

| Token | Value | Use |
|---|---|---|
| `--primary` | `#5865F2` | Brand, active nav, primary buttons, focus rings |
| `--primary-hover` | `#7984F5` | Primary hover |
| `--primary-dim` | `rgba(88,101,242,0.14)` | Active nav bg, selected-row bg, focus glow |
| `--primary-soft` | `rgba(88,101,242,0.22)` | Active nav inner border |
| `--success` | `#2ebd7f` | Watched dots, success result, connected pill |
| `--danger` | `#f04c5c` | Unwatched dots, delete button, error result |
| `--warning` | `#f4a833` | Dry-run badge, required-field tag |
| `--info` | `#4fa9e8` | Info pills, "live" mode badge |
| `--watched` | `#2ebd7f` | Watch dot — watched |
| `--unwatched` | `#f04c5c` | Watch dot — unwatched |
| `--unknown` | `#4d5566` | Watch dot — not in Jellyfin |

### Colors — service identity dots

Used as small 8px glowing dots next to each *arr service's name (page eyebrow + settings card header).

| Token | Value | Service |
|---|---|---|
| `--radarr` | `#ffc135` | Radarr (Movies) |
| `--sonarr` | `#2ec4b6` | Sonarr (Series) |
| `--lidarr` | `#6b8af3` | Lidarr (Music) |
| `--jellyfin` | `#aa5cc3` | Jellyfin (watch source) |

### Typography

Two Google Fonts:

```html
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

| Token | Stack |
|---|---|
| `--font-sans` | `'Geist', system-ui, -apple-system, 'Segoe UI', sans-serif` |
| `--font-mono` | `'Geist Mono', ui-monospace, 'SF Mono', Menlo, monospace` |

Base body: `14px / 1.5` Geist, `font-feature-settings: 'cv11', 'ss01'`, antialiased.

**Type scale (all in px):**
- Page title (`h1.page-title`): 26px / 600 / -0.02em tracking
- Card / section heading (`h2`): 15–17px / 600
- Eyebrow (`.page-eyebrow`, `.drawer-eyebrow`, `.drawer-section-title`): 11px / 600 / +0.08em / uppercase
- Body: 14px / 400
- Table cell: 13.5px
- Sub-table cell: 13px
- Pill / badge: 11px / 600 / +0.04em / uppercase
- Small / hint: 11.5–12.5px
- Stat value (logs page summary): 22px / 600 / -0.02em

**Use mono for:** all numeric columns (year, size, count), timestamps, API keys, file paths, URLs, and stat values. Add class `.mono` (which sets `font-family: var(--font-mono); font-feature-settings: 'tnum' 1;`).

### Spacing & radii

| Use | Value |
|---|---|
| Page padding | `28px 32px 80px` (top/sides/bottom) |
| Max page width | `1240px`, centered |
| Card / table radius | `10px` |
| Button radius | `7px` (`6px` for size=sm) |
| Pill radius | `4px` |
| Checkbox radius | `4px` |
| Row padding (cozy) | `10px 14px` |
| Row padding (compact) | `6px 14px` |
| Filter bar padding | `14px 16px` |
| Card body padding | `16px 18px` |
| Card header padding | `14px 18px` |

### Shadows / effects

- Watched dot: `box-shadow: 0 0 6px rgba(46,189,127,0.4)`
- Unwatched dot: `box-shadow: 0 0 6px rgba(240,76,92,0.4)`
- Service dots (radarr/sonarr/lidarr/jellyfin): `box-shadow: 0 0 8px var(--<service>)`
- Connection indicator dot: `box-shadow: 0 0 0 3px rgba(46,189,127,0.18)` (ring)
- Drawer backdrop: `rgba(8,10,14,0.65)` + `backdrop-filter: blur(2px)`
- Top nav: `backdrop-filter: blur(8px)`, sticky `top:0`
- Primary button: `inset 0 1px 0 rgba(255,255,255,0.12)` (subtle top highlight)

## Layout — global chrome

### Top nav (`nav.top-nav`)

Sticky, 56px tall, full-width, `linear-gradient(to bottom, #14181f, #11151c)` background, bottom border `--border`.

Three slots, left to right:
1. **Brand** — `<a class="brand">` with 22px logo mark + word "Selectarr" (Geist 600, 15px). The mark is a flat purple disc holding a stylised white trash bin with a red checkmark inside ("Bin & Check"), reading at small sizes and fitting visually next to the other *arr-suite icons. SVG (200×200 viewBox, scale to 22px in the nav):
   ```html
   <svg viewBox="0 0 200 200" width="22" height="22" aria-hidden="true">
     <circle cx="100" cy="100" r="92" fill="var(--primary)"/>
     <rect x="84" y="56" width="32" height="8" rx="3" fill="#ffffff"/>
     <rect x="52" y="68" width="96" height="14" rx="4" fill="#ffffff"/>
     <path d="M60 90 L140 90 L132 152 Q132 156 128 156 L72 156 Q68 156 68 152 Z"
           fill="#ffffff"/>
     <path d="M76 119 L92 137 L124 105"
           fill="none" stroke="#F04C5C" stroke-width="11"
           stroke-linecap="round" stroke-linejoin="round"/>
   </svg>
   ```
   The full-size source is included in this bundle as `Selectarr Logo Variant 1.svg` — use that for favicons, social cards, and any size > 32px.
2. **Nav tabs** (`.nav-tabs > .nav-tab`) — Movies / Series / Music / Activity / Settings. Each is an icon + label, 13.5px / 500. Inactive: `--text-muted` on transparent; hover: `--text` on `--surface`; active: `--text-strong` on `--primary-dim` with inset 1px `--primary-soft` border, icon colored `--primary`.
3. **Right rail** (`.nav-right`) — `DRY-RUN` warning pill (only when `dry_run=true`) + a small mono "connection" line listing connected services with a green pulsing dot.

Below ~1080px viewport: hide tab labels, keep icons.

### Page container

`<main class="page">` — max-width 1240px, 28px top padding, 32px horizontal, 80px bottom.

### Page header (`.page-header`)

Flex row, items flex-end. Left column:
- Eyebrow (`.page-eyebrow`) — service tag with dot, e.g. `● Radarr`, in 11px uppercase muted text
- Title (`.page-title`) — 26px Geist 600 strong
- Subtitle (`.page-subtitle`) — 13.5px muted, max-width 64ch

Right column: optional action buttons.

22px margin-bottom from page content.

## Screens

### 1. Movies (`/movies`)

**Purpose:** browse Radarr's library, multi-select movies to delete in bulk.

**Layout:**
1. Page header — eyebrow `● Radarr` (radarr dot), title "Movies", subtitle "Browse and selectively delete movies. Files are removed via Radarr and added to the import exclusion list."
2. Filter bar (`.filter-bar`) — surface bg, 10px radius, contains:
   - "Filter" select (5 options: All / Watched by all / Watched by any / Watched by selected user / Not watched by anyone)
   - "User" select (— all users — + each Jellyfin user)
   - Spacer (`flex:1`)
   - Count: `<span class="mono">{count}</span> <span class="muted">movies</span>`
3. Banners (only when present) — service error / dry-run notice / jellyfin warning above the filter bar
4. Table card (`.table-card`) — surface, 10px radius, contains `.data-table`:
   - Header row, uppercase 11px `--text-dim` on `--bg-elevated`
   - Columns: `[checkbox 36px] [Title] [Year 60px mono] [Size 100px mono muted] [Watched 100px]`
   - Row hover: `--surface-2`. Selected row: `--primary-dim` bg with 2px `--primary` inset-left
   - Movies without a file: no checkbox (em-dash `—` in dim color), append `<span class="pill pill-muted">no file</span>` after title
   - "Watched" column renders one `WatchDots` component per row — see Components below
5. Action row (`.action-row`) — surface card below the table, flex row:
   - Left: selected count + total size to free (mono numbers)
   - Right: danger button "Preview deletion" (in dry-run) or "Delete selected" (live), with trash icon. Disabled when nothing selected.

**Interactions:**
- Header checkbox: toggle-all visible-with-file movies. Indeterminate state when some-but-not-all selected.
- Click row checkbox: toggle that movie's selection.
- "Preview deletion" / "Delete selected" → opens the confirm drawer (see Section 6).
- Changing filter or user select fires `hx-get="/movies/list"` and replaces `#movies-container`.

### 2. Series (`/series`)

**Purpose:** delete at series, season, or individual episode level. Nested expand structure.

**Layout:**
1. Page header — eyebrow `● Sonarr`, title "Series", subtitle "Delete at series, season, or individual episode level."
2. Filter bar (same as Movies)
3. Table card with nested expansion:
   - **Top-level series row:** `[chevron 28px] [Title] [Year 60px mono] [Seasons 80px mono] [Size 100px mono muted] [Watched 100px] [Actions 140px right-aligned]`
   - Click chevron → expand row in-place, revealing seasons sub-table
   - Actions column: ghost-danger "Delete series" button with trash icon
   - Expanded row gets `.row-expanded` (background `--surface-2`)
4. **Seasons sub-table** (`.data-table-sub` inside `.nested-wrap`):
   - Indented `padding: 4px 24px 12px 56px` from series row, in `--bg-elevated`
   - Smaller table radius (8px), surface bg, slightly smaller font (13px)
   - Columns: `[chevron] [Season N] [Episodes — `8/8` mono with dim slash] [Delete season]`
5. **Episodes sub-sub-table** (`.nested-wrap-inner`, further indented 36px):
   - Columns: `[checkbox] [Ep number 2-digit mono "01"] [Title] [File ✓ or —]`
   - Below the table, right-aligned: red "Delete {N} episodes" button (disabled when none selected)

**Visual hierarchy:** each nesting level uses `--bg-elevated` as a backdrop, while the inner table itself sits on `--surface` — this creates a subtle two-tone stripe that reads as containment without heavy borders.

### 3. Music (`/music`)

**Purpose:** delete artists, albums, or individual tracks. Two-level expansion (artist → albums).

**Layout:**
1. Page header — eyebrow `● Lidarr`, title "Music", subtitle "Delete artists, albums, or individual tracks."
2. Filter bar
3. Table card:
   - Artist row: `[chevron] [Artist name] [Albums count mono] [MusicBrainz — pill "linked" (info tone) or "none" (muted)] [Delete artist]`
   - Expanded → albums sub-table with columns: `[Album title] [Year mono] [Tracks mono] [Files ✓/—] [Delete album]`

### 4. Activity (`/logs`)

**Purpose:** audit log of every deletion attempt (live + dry-run).

**Layout:**
1. Page header — eyebrow `/var/log/selectarr` (mono small muted), title "Activity", subtitle "Every deletion is logged here with timestamp, scope, mode, and result." Right action: filter select (All / Errors only / Live runs / Dry-runs) + secondary "Clear log" button.
2. **Stats summary row** (`.logs-summary`) — 4-column grid of `.stat` cards (`--surface`, 8px radius, 12×14 padding):
   - Entries (neutral)
   - Succeeded (mono 22px in `--success`)
   - Failed (mono 22px in `--danger`)
   - Dry-runs (mono 22px in `--warning`)
3. Table card with columns: `[Timestamp 175px mono muted] [Type 100px — colored pill] [Title + message subtext muted small] [Mode 100px — "dry-run" warning pill or "live" info pill, both with dot] [Result 90px — green ✓ OK or red ✕ error]`

Empty state: centered `.empty-state` text "No log entries match the current filter."

### 5. Settings (`/settings`)

**Purpose:** configure service URLs + API keys, toggle behaviour flags.

**Layout:**
1. Page header — eyebrow `~/config/config.yaml` (mono small muted), title "Settings", subtitle explaining `config.yaml` location and which services are required vs optional.
2. **Settings grid** (`.settings-grid`) — 2-column responsive grid (collapses to 1 below 1080px), one `.service-card` per service:
   - Card header: `[service dot] [Service name h2] [kind tag "required" (warning) or "optional" (muted)]` + muted description below ("Watch-status source" / "Movies" / "Series, seasons, episodes" / "Artists, albums, tracks")
   - Card body (stacked, 14px gap): URL input (mono) + API key input (mono, type=password) + a row with secondary "Test connection" button (plug icon) and a status pill (`connected` / `failed` / `testing…` / `not tested`).
3. **Behaviour card** — full-width below the grid. Card body stacks two `Toggle` controls:
   - "Dry-run mode" — hint "Simulate every deletion without touching any files. Recommended while you tune filters."
   - "Add to import exclusion list" — hint "Prevent deleted items from being re-downloaded by Radarr / Sonarr / Lidarr."
4. Submit button below cards (omit if you persist via HTMX inline saves).

### 6. Confirm drawer (overlay)

Right-side drawer (460px wide, full-height), used whenever the user triggers a deletion. Three phases driven by HTMX swaps:

- **Phase 1 — confirm** (server returns `partials/confirm_*.html` into `#delete-area`):
  - Header eyebrow "Dry-run preview" or "Confirm deletion"; h2 "Review before delete"
  - Banner: warning ("Dry-run mode is on…") or error ("This will permanently delete files. Files are removed from disk by the source *arr service. This cannot be undone.")
  - 3-stat strip: Scope (e.g. "movies"), Items (mono count), Would free / Will free (mono size)
  - Drawer-list of items: title left, size mono muted right
  - Footer: secondary "Cancel" + danger "Run simulation" / "Delete now"
- **Phase 2 — working**: spinner + "Simulating deletion…" / "Deleting files…" (purely visual; HTMX request indicator covers this)
- **Phase 3 — result** (server returns `partials/delete_result.html`):
  - Banner: info "Dry-run complete." or success "Deletion complete."
  - Result list with each item + green ✓ "would delete" / "deleted"
  - Footer: primary "Close"

Backdrop: `rgba(8,10,14,0.65)` with `backdrop-filter: blur(2px)`. Click backdrop or close icon to dismiss.

Animation: backdrop fades in over 120ms; drawer slides in 24px from the right over 180ms (`cubic-bezier(.2,.7,.3,1)`).

## Components

These reusable bits appear across multiple pages. Class names below match `styles.css`.

### `BrandMark` — logo mark
Inline SVG (see Top nav). Single prop: size (default 22px).

### `WatchDots`
Renders one `<span class="dot">` per Jellyfin user, colored green/red/gray based on watch state for that user. Tooltip (`title=`) shows `{user} · watched/unwatched/unknown`. If `watch_status` is null (not in Jellyfin), render a single gray dot.

```html
<span class="watch-dots">
  <span class="dot dot-watched"   title="sven · watched"></span>
  <span class="dot dot-unwatched" title="nora · unwatched"></span>
  <span class="dot dot-watched"   title="roel · watched"></span>
</span>
```

Dot: 10px circle, watched/unwatched dots get a colored glow (`box-shadow: 0 0 6px <color@40%>`), unknown dot is flat `#4d5566`.

### `Pill` — small badge
`<span class="pill pill-{tone}">` with optional leading dot (`<span class="pill-dot">`). Tones: `primary`, `accent`, `success`, `danger`, `warning`, `info`, `muted`. 11px / 600 / +0.04em / uppercase. Used for: type tags in logs, mode badges, connection status, "no file" markers, DRY-RUN nav badge, service-kind tags.

### `Banner` — inline notice
`<div class="banner banner-{tone}">` with circular icon on the left (`!` for warning/error, `i` for info, `✓` for success), then bold title + muted body. Tones: `error` (red), `warning` (amber), `info` (blue), `success` (green). All use 6% tint of their accent as background + 30% as border.

### `Button`
`<button class="btn btn-{variant} btn-{size}">`:
- **primary** — solid `--primary`, white text, subtle inset top highlight
- **secondary** — `--surface-2` bg, `--border-strong` border
- **danger** — solid `--danger`, white text
- **ghost-danger** — transparent, hovers to red text on `--danger-dim` bg. Use for inline "Delete X" buttons inside table rows.
- Sizes: default (8×14 padding, 13.5px) or `sm` (5×10, 12.5px, 6px radius)
- Optional leading icon via `<span class="btn-icon">` containing an inline SVG (see "Icons" below)

### `Checkbox`
Custom-styled 16px square. Hidden native input + visible `<span class="cb-box">` containing two SVG glyphs (`.cb-check` and `.cb-dash`) that show/hide based on `:checked` / `:indeterminate` state. Border `--border-strong` when off; primary fill when on. Hover state: border becomes `--primary`.

### `Toggle`
36×20 pill track with 14px thumb. Off: track `--surface-3` / `--border-strong` border, thumb `--text-muted`. On: track + border `--primary`, thumb white, translated 16px right. Supports an inline label + hint to the right of the track.

### `Select`
Custom-styled. Wrapper `.select-wrap` contains the native `<select>` (appearance:none, padded 8×11, padding-right 28px) + a positioned `▾` caret. Focus ring: 3px `--primary-dim` glow.

### `TextInput`
`<input class="input">` with optional `.mono` class for URLs/keys. Same focus ring as Select. Label above (`.field-label`, 11.5px / 500 muted), optional `required` tag (warning amber chip) and `.field-hint` below.

### Icons
Inline SVGs in 16×16 viewBox, `stroke="currentColor"`, `fill="none"`, `stroke-width="1.4"`. Set listed below; all present in `components.jsx` under the `Icon` export. Reproduce them as Jinja macros or as a small SVG sprite.

| Icon | Use |
|---|---|
| `Film` | Movies nav tab |
| `Tv` | Series nav tab |
| `Music` | Music nav tab |
| `Log` | Activity nav tab |
| `Cog` | Settings nav tab |
| `Chevron` | Expand/collapse rows (rotates 90° when `open`) |
| `Trash` | All delete buttons |
| `Check` | File-present indicator, success result |
| `X` | Error result, drawer close |
| `Plug` | Test connection button |

## Interactions & Behavior

### Filter bar
- Changing filter or user select triggers an HTMX request to the page's `/list` endpoint (existing pattern); use `hx-include` to bundle both selects so they always submit together.
- Loading indicator: tiny "Loading…" muted text in the filter-bar-spacer slot, visible while `htmx-request` class is on `body` or the filter form.

### Row expansion
- Chevron button toggles a class on the row + reveals the nested `<tr class="row-nested">` containing the sub-table.
- In HTMX: `hx-get="/series/{id}/seasons"` with `hx-target` pointing at an empty placeholder div in the nested row; chevron rotates via CSS (`transform: rotate(90deg)` when `data-open="true"` is set on the trigger button — or use `htmx:afterSettle` to flip a class).

### Confirm drawer flow
1. User clicks delete trigger (movies bulk, series row action, season action, episode bulk, artist/album action).
2. HTMX POST to `/{movies|series|music}/confirm` with the selected IDs. Server returns `partials/confirm_*.html` rendered as the drawer body (no chrome change — the drawer container is always in the DOM, just `aria-hidden="true"` until populated).
3. Backdrop: a CSS sibling of the drawer; toggle a `.drawer-open` class on `<body>` to fade it in.
4. Confirm-click POSTs to `/{type}/delete`. While waiting, swap to the working state (spinner). On response, swap to the result state.

### Selection state
- Movies page: server doesn't need to track selection — the form posts all checked IDs in one request, so use a normal `<form>` with `name="radarr_ids"` checkboxes (already the pattern in the existing partial).
- Episodes selection inside a season: same — a scoped `<form id="ep-form-{series}-{season}">` with `hx-include="closest form"`.

### Connection test
- "Test connection" button posts to `/settings/test/{service}` with the URL+key, server returns just the status pill HTML to swap into the inline status span.
- During the request, swap to a `Pill tone="info"` "testing…". Existing `htmx-indicator` pattern works.

### Animations
- Chevron rotation: 150ms `ease`
- Row hover background: 100ms
- Button background/border: 120ms
- Toggle thumb translate: 150ms
- Drawer slide: 180ms `cubic-bezier(.2,.7,.3,1)` from `translateX(24px) opacity:0`
- Backdrop fade: 120ms

## Responsive

- ≥1080px: full layout
- <1080px: settings grid collapses to 1 column; logs summary collapses to 2×2; nav tabs hide their text labels (icon-only)
- <720px: page padding shrinks to `20px 14px 60px`; filter bar wraps; top nav gaps tighten; connection status hides

## State Management

The existing app keeps state on the server (HTMX swaps). Don't introduce client-side state where the server already owns it. Specifically:

- **Filter + user selects**: re-fetched server-side on every change
- **Expansion state**: stateless — the chevron just triggers a `hx-get` that injects markup; collapsing simply clears that container's innerHTML (`hx-swap="innerHTML"` + a second click empties it, or use `hx-trigger="click consume"` and stash the markup in a hidden div)
- **Selection state**: lives in the form's checkbox state until submit
- **Confirm drawer phases**: each phase is a server-rendered partial swapped into `#delete-area`

The only purely client-side concern is the drawer backdrop visibility — toggle a class on `<body>` via `hx-on::after-swap` when `#delete-area` becomes non-empty.

## Assets

- **Logo** — `Selectarr Logo Variant 1.svg` (in this bundle). Flat purple disc + white trash bin + red check inside. Use this as the master file for favicons (export 32×32, 48×48, 180×180 from it), social cards, and any place that needs a sharper or larger version than the inline 22px nav mark. The inline SVG in the nav is a hand-tuned subset of the same artwork.
- **Icons** — all inline SVGs in `components.jsx` (see "Icons" section above). Reproduce as Jinja macros or a tiny SVG sprite. No external icon libraries.
- **Fonts** — Geist + Geist Mono from Google Fonts.
- No raster images, no other binary assets.

## Files in this bundle

| File | Purpose |
|---|---|
| `Selectarr UI.html` | Entry point — open in a browser to see the prototype |
| `styles.css` | **The canonical stylesheet** — port this directly. All tokens, all component styles. |
| `components.jsx` | Shared React components (`BrandMark`, `WatchDots`, `Pill`, `Banner`, `Button`, `Select`, `TextInput`, `Checkbox`, `Toggle`, `Icon`, `fmt`). Reference for the exact SVG icon paths, dot rendering logic, and watch-status formatting. |
| `pages.jsx` | The five page components + `ConfirmDrawer`. Reference for column layouts, copy, empty states, and the deletion flow. |
| `app.jsx` | Top nav + router + tweaks. Reference for the nav structure. |
| `data.js` | Mock data — useful as a reference for the data shape each page expects from the backend. |
| `tweaks-panel.jsx` | Prototype-only tooling for live design tweaks. **Do not port.** |
| `Selectarr Logo Variant 1.svg` | The chosen brand mark at full fidelity (200×200 viewBox). Master file for favicons, social cards, etc. |

## Implementation Plan (suggested)

1. Add Geist + Geist Mono `<link>` to `base.html`.
2. Replace the inline `<style>` block in `base.html` with `<link rel="stylesheet" href="/static/css/selectarr.css">` and copy `styles.css` to `app/static/css/`. Mount a `StaticFiles` route if not already present.
3. Rewrite the top-nav markup in `base.html` to match `.top-nav` / `.nav-tab` / `.brand` / `.nav-right` structure.
4. Update each page template (`movies.html`, `series.html`, `music.html`, `logs.html`, `settings.html`) to use the new wrapper classes (`.page-header`, `.filter-bar`, `.table-card`, etc.) — most existing HTMX attributes carry over unchanged.
5. Rewrite each partial (`partials/*_list.html`) to emit the new table markup, custom checkbox HTML, and watch-dots structure.
6. Add a fixed `<aside class="drawer">` to `base.html` (initially `hidden`) and update the confirm/result partials to populate it; add the body-class toggle via `hx-on`.
7. Verify each route renders cleanly against the prototype screenshots, page by page.

## Notes & Caveats

- The prototype's tab switching uses React state; in the real app, each tab is a Jinja-rendered route (`/movies`, `/series`, …) — no SPA behaviour to replicate.
- The "connection" pulse in the top-right of the nav is decorative in the prototype; for the real app, derive it from each service's last-known connection state from settings (a server-side `connected_services` context var would do it).
- The accent color `#5865F2` was chosen with the user. Keep it as a CSS variable so it can be re-themed without touching components.
- The prototype shows DRY-RUN mode on by default — this matches the project's default config.
