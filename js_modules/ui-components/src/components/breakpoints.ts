/**
 * Shared viewport breakpoints.
 *
 * CSS custom properties cannot be used inside `@media` queries, so CSS modules
 * must hardcode these values. Keep any `@media (max-width: ...)` rules in sync
 * with the constants here.
 */

// Phone/small-tablet widths. At or below this width, the app switches to
// mobile chrome (e.g. the left nav becomes an overlay drawer).
export const MOBILE_BREAKPOINT_PX = 768;

// "Small laptop" width used by LayoutProvider to auto-close the left nav.
export const SMALL_SCREEN_BREAKPOINT_PX = 1440;
