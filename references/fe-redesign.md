# Pipeline Design System Overhaul

## Status: Phase 1 Complete

Phase 1 (color system + component migration) is complete. Phase 2 (nav icon sidebar) is deferred.

---

## Objective
Transform Pipeline into a cohesive, warm, and professional application with:
1. Burnt orange brand color palette with warm neutrals and teal accents
2. Centralized color system via Tailwind v4 `@theme` block
3. Centered content layout (max-width ~896px / `max-w-4xl`)
4. Consistent button hierarchy and improved input visibility
5. Light, airy feel with warm personality

## Color Palette

**Personality: Supportive Momentum**
A job search is stressful—our palette should feel like a capable friend, not a corporate wall. Warm and human, but organized and trustworthy.

### Brand/Primary
- **Burnt Orange**: `#C2552D` — Action, energy, forward progress, CTAs

### Backgrounds
- **Warm Cream**: `#F7F4F1` — main page background
- **Off-White**: `#FEFCFB` — sidebar, secondary surfaces
- **Pure White**: `#FFFFFF` — cards, inputs, elevated surfaces

### Text Colors
- **Charcoal**: `#2D2926` — primary text, headings
- **Medium Gray**: `#5C5651` — body text
- **Light Gray**: `#8A847E` — secondary text, muted content

### Accent Colors
- **Deep Teal**: `#1A7B7A` — Trust, stability, editing states
- **Soft Sage**: `#87A96B` — Progress, completion
- **Muted Amber**: `#E09F3E` — Warnings without panic

### Borders & Dividers
- **Light Border**: `#C7C4C0` — subtle dividers
- **Medium Border**: `#A89F91` — defined borders

### State Colors
- **Success**: Burnt Orange `#C2552D`
- **Progress/Complete**: Soft Sage `#87A96B`
- **Warning**: Muted Amber `#E09F3E`
- **Error**: Deep Red `#B83C3C`
- **Info**: Deep Teal `#1A7B7A`

## Implementation (Tailwind v4)

Colors are defined in a single `@theme` block in `src/index.css`. No `tailwind.config.js` needed. This gives native Tailwind v4 classes like `bg-brand-primary`, `bg-brand-primary/50`, `text-teal`, etc. with built-in alpha support.

### Button Hierarchy
- **Primary**: `bg-brand-primary text-white` — main actions
- **Secondary**: Teal outline with teal text — alternative actions
- **Tertiary**: Charcoal text only — low-priority options
- **Ghost**: Light gray text with subtle hover — utility actions
- **Danger**: Error outline with error text

### Badge Variants (warm-tinted)
- **emerald** (STRONG PURSUE): `bg-sage/10 text-sage ring-sage/20`
- **blue** (PURSUE): `bg-teal/10 text-teal ring-teal/20`
- **amber** (PASS): `bg-amber/10 text-amber ring-amber/20`
- **rose** (HARD PASS): `bg-error/10 text-error ring-error/20`
- **gray** (neutral): `bg-border-light/30 text-text-body ring-border-medium/20`
- **indigo** (info): `bg-brand-primary/10 text-brand-primary ring-brand-primary/20`

### Status Dots
- pending: `bg-border-medium`
- running: `bg-teal animate-pulse`
- complete: `bg-sage`
- failed: `bg-error`

### Editing State
- CollapsibleCard uses **teal** for editing border/ring (differentiates from primary action buttons)
- Toolbar active states use `bg-brand-primary/10 text-brand-primary`

## Completed Changes

| File | Change |
|---|---|
| `tailwind.config.js` | **Deleted** — Tailwind v4 uses @theme in CSS |
| `src/index.css` | Replaced CSS vars with `@theme` block (hex values) |
| `src/components/SectionNav.tsx` | Design-system colors for status dots, active/hover states, group headers |
| `src/components/ui/CollapsibleCard.tsx` | Teal editing state, design-system borders/text |
| `src/components/ui/Input.tsx` | `border-border-light`, `border-error/50` |
| `src/components/ui/Badge.tsx` | Warm-tinted variants using sage/teal/amber/error |
| `src/pages/RoleDetailPage.tsx` | `bg-off-white` sidebar, `bg-cream` main, `max-w-4xl`, design-system text/links |
| `src/pages/NewJobPage.tsx` | `text-text-primary` heading |
| `src/components/SectionPanel.tsx` | Status dots, edit/save/cancel buttons, prose text, error/status text |
| `src/components/SectionEditor.tsx` | `border-border-light`, `bg-off-white` toolbar, brand-primary active states |
| `src/components/ui/ConfirmModal.tsx` | `text-text-primary` title, `text-text-body` description |
| `src/components/ui/Dropdown.tsx` | Design-system borders, text, active states |
| `src/components/ui/SegmentedControl.tsx` | `bg-cream` track, design-system text |
| `src/components/ui/IconButton.tsx` | `text-text-secondary`, `hover:bg-cream`, `ring-brand-primary` |
| `src/components/ui/EmptyState.tsx` | Design-system text colors |
| `src/components/ui/Skeleton.tsx` | `bg-border-light/30`, `border-border-light/50` |

**No hardcoded gray/indigo/blue/green/red/emerald/rose Tailwind color classes remain in .tsx files.**

## Deferred: Phase 2 — Nav Icon Sidebar

Will cover in a separate plan:
- Icon mapping per section type (using @heroicons/react)
- Three states: collapsed / narrow (64px icons) / wide (280px icons+text)
- Responsive breakpoints
- Toggle button placement
- "Generate Cover Letter" behavior in narrow mode
- Animation transitions
- State persistence (localStorage)
