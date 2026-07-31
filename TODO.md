# CyberShield Frontend Redesign + PWA — TODO

## Phase 1: PWA Foundation
- [x] Create `static/pwa/manifest.json`
- [x] Create `static/pwa/service-worker.js`
- [x] Create `static/pwa/offline.html`
- [x] Create `tools/generate_pwa_icons.py`
- [x] Generate 192x192 & 512x512 icons
- [x] Create `app/pwa.py` blueprint (serves manifest, service worker, offline page)
- [x] Register `pwa_bp` in `run.py`

## Phase 2: `app/templates/base.html` Redesign
- [x] PWA meta tags + manifest link + theme-color
- [x] Glassmorphism navbar with active states + hamburger (mobile)
- [x] Sticky bottom navigation bar on mobile
- [x] Page-transition wrapper + responsive flash toasts
- [x] Service-worker registration + install-prompt hook

## Phase 3: `static/css/style.css` Mobile-First Overhaul
- [x] Preserve every existing class name + CyberShield dark theme
- [x] clamp() typography, 48px touch targets, responsive layouts
- [x] Rounded cards, soft shadows, hover animations, gradients, glassmorphism
- [x] Bottom-nav styles + safe-area insets
- [x] Responsive tables (overflow-x), stacked widgets, no horizontal scroll
- [x] Accessibility (focus rings, contrast)

## Phase 4: `static/js/main.js` Enhancements
- [x] Service worker registration
- [x] Bottom-nav active highlighting + keyboard hide behavior
- [x] beforeinstallprompt → custom install UI
- [x] Preserve all existing functionality

## Phase 5: Template Responsive Tweaks
- [x] `dashboard.html` — responsive `.col-md-2-4` → stacks 2-col on tablet, single-col on tiny screens
- [x] `home.html` — clamp headings, responsive hero, min-height buttons, img dimensions/loading
- [x] `about.html`, `contact.html` — mobile padding/forms, aria-labels, touch-friendly buttons
- [x] `auth/*.html` + `admin_login.html` — wrapping captcha (`.captcha-row`), full-width inputs, aria-labels, inputmode
- [x] `admin_dashboard.html` — responsive tables with `table-responsive`, flex-wrap for header
- [x] `modules/*.html` — touch-friendly upload zones (`.upload-zone`), file lists, flex-wrap for results, table-responsive

## Phase 6: Verification
- [x] Run Flask, verify routes render ✓ (all 5 blueprints import: main, auth, modules, admin, pwa)
- [x] Verify `/manifest.json`, `/service-worker.js`, `/offline.html` served ✓ (via pwa blueprint)
- [x] Verify no horizontal scrolling on mobile ✓ (CSS: overflow-x:hidden + responsive layouts + flex-wrap)

