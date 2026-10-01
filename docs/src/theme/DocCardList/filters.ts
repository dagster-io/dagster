// Pure filter helpers for the integrations libraries index page.
//
// These are kept free of React and Docusaurus hooks so they can be unit-tested in isolation.
// Each tag corresponds to a boolean set in a card's `sidebar_custom_props`: `DocCard` renders it as
// a pill, and a filter button narrows the card list down to the cards carrying it.

export type CardTagKey = 'community' | 'component' | 'componentAvailable';

export type ItemCustomProps = {customProps?: Partial<Record<CardTagKey, boolean>>};

export type CardTag = {
  key: CardTagKey;
  label: string;
};

// Pill copy, rendered by `DocCard` next to the card title.
export const CARD_TAGS: readonly CardTag[] = [
  {key: 'community', label: 'Community'},
  {key: 'component', label: 'Component'},
  {key: 'componentAvailable', label: 'Component available'},
];

export type FilterKey = 'community' | 'component';

// A filter can catch more than one tag. The filter bar stays coarse — just Community and Component —
// while cards distinguish "Component" from "Component available", so the single Component button has
// to return every integration that has a component, however its card is labeled.
export type Filter = {
  key: FilterKey;
  label: string;
  tags: readonly CardTagKey[];
};

export type ActiveFilters = Partial<Record<FilterKey, boolean>>;

export const FILTERS: readonly Filter[] = [
  {key: 'community', label: 'Community', tags: ['community']},
  {key: 'component', label: 'Component', tags: ['component', 'componentAvailable']},
];

export function hasCardTag(item: ItemCustomProps, key: CardTagKey): boolean {
  return item.customProps?.[key] === true;
}

function matchesFilter(item: ItemCustomProps, filter: Filter): boolean {
  return filter.tags.some((tag) => hasCardTag(item, tag));
}

// Filters are only surfaced on the integrations libraries index page.
export function isLibrariesPath(pathname: string): boolean {
  return pathname.replace(/\/$/, '').endsWith('/integrations/libraries');
}

// Only show a filter when there is at least one matching item to narrow down to, and only on the
// libraries index page.
export function computeAvailableFilters(items: ItemCustomProps[], pathname: string): Filter[] {
  if (!isLibrariesPath(pathname)) {
    return [];
  }
  return FILTERS.filter((filter) => items.some((item) => matchesFilter(item, filter)));
}

// An item is shown when it matches every active filter (intersection / AND). Filters that are not
// currently active, or not available, impose no constraint.
export function matchesActiveFilters(
  item: ItemCustomProps,
  availableFilters: readonly Filter[],
  activeFilters: ActiveFilters,
): boolean {
  return availableFilters.every((filter) => !activeFilters[filter.key] || matchesFilter(item, filter));
}
