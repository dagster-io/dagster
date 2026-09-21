import {describe, expect, it} from 'vitest';

import {
  CARD_TAGS,
  FILTERS,
  type FilterKey,
  type ItemCustomProps,
  computeAvailableFilters,
  hasCardTag,
  isLibrariesPath,
  matchesActiveFilters,
} from './filters';

const community: ItemCustomProps = {customProps: {community: true}};
const component: ItemCustomProps = {customProps: {component: true}};
const componentAvailable: ItemCustomProps = {customProps: {componentAvailable: true}};
const communityComponent: ItemCustomProps = {customProps: {community: true, component: true}};
const plain: ItemCustomProps = {customProps: {}};
const noProps: ItemCustomProps = {};

const filterByKey = (key: FilterKey) => {
  const filter = FILTERS.find((f) => f.key === key);
  if (!filter) {
    throw new Error(`no filter with key ${key}`);
  }
  return filter;
};

describe('CARD_TAGS', () => {
  it('has pill copy for every tag a filter can catch', () => {
    const tagKeys = CARD_TAGS.map((tag) => tag.key);
    for (const filter of FILTERS) {
      for (const tag of filter.tags) {
        expect(tagKeys).toContain(tag);
      }
    }
  });

  it('labels the component tags distinctly', () => {
    expect(CARD_TAGS.find((tag) => tag.key === 'component')?.label).toBe('Component');
    expect(CARD_TAGS.find((tag) => tag.key === 'componentAvailable')?.label).toBe('Component available');
  });
});

describe('FILTERS', () => {
  it('keeps the filter bar coarse even though the pills are split', () => {
    expect(FILTERS.map((f) => f.label)).toEqual(['Community', 'Component']);
  });

  it('points the single Component filter at both component tags', () => {
    expect(filterByKey('component').tags).toEqual(['component', 'componentAvailable']);
  });
});

describe('hasCardTag', () => {
  it('is true only when the prop is explicitly set', () => {
    expect(hasCardTag(component, 'component')).toBe(true);
    expect(hasCardTag(component, 'componentAvailable')).toBe(false);
    expect(hasCardTag(plain, 'community')).toBe(false);
    expect(hasCardTag(noProps, 'community')).toBe(false);
  });
});

describe('isLibrariesPath', () => {
  it('matches the libraries index page with and without a trailing slash', () => {
    expect(isLibrariesPath('/integrations/libraries')).toBe(true);
    expect(isLibrariesPath('/integrations/libraries/')).toBe(true);
  });

  it('does not match an individual library page or unrelated pages', () => {
    expect(isLibrariesPath('/integrations/libraries/dbt')).toBe(false);
    expect(isLibrariesPath('/integrations')).toBe(false);
    expect(isLibrariesPath('/guides')).toBe(false);
  });
});

describe('computeAvailableFilters', () => {
  it('returns no filters when off the libraries page, even with matching items', () => {
    expect(computeAvailableFilters([community, component], '/integrations/libraries/dbt')).toEqual([]);
  });

  it('only surfaces a filter when at least one item matches it', () => {
    const available = computeAvailableFilters([component, plain], '/integrations/libraries');
    expect(available.map((f) => f.key)).toEqual(['component']);
  });

  it('surfaces the component filter for either component tag', () => {
    const available = computeAvailableFilters([componentAvailable, plain], '/integrations/libraries');
    expect(available.map((f) => f.key)).toEqual(['component']);
  });

  it('surfaces every filter that has a match', () => {
    const available = computeAvailableFilters([community, component], '/integrations/libraries');
    expect(available.map((f) => f.key)).toEqual(['community', 'component']);
  });

  it('returns no filters when nothing matches', () => {
    expect(computeAvailableFilters([plain, noProps], '/integrations/libraries')).toEqual([]);
  });
});

describe('matchesActiveFilters', () => {
  const available = FILTERS;

  it('shows all items when no filter is active', () => {
    expect(matchesActiveFilters(plain, available, {})).toBe(true);
    expect(matchesActiveFilters(component, available, {})).toBe(true);
  });

  it('catches both component categories under one filter', () => {
    const active = {component: true};
    expect(matchesActiveFilters(component, available, active)).toBe(true);
    expect(matchesActiveFilters(componentAvailable, available, active)).toBe(true);
    expect(matchesActiveFilters(communityComponent, available, active)).toBe(true);
    expect(matchesActiveFilters(community, available, active)).toBe(false);
    expect(matchesActiveFilters(plain, available, active)).toBe(false);
  });

  it('intersects multiple active filters (AND, not OR)', () => {
    const active = {community: true, component: true};
    expect(matchesActiveFilters(communityComponent, available, active)).toBe(true);
    expect(matchesActiveFilters(community, available, active)).toBe(false);
    expect(matchesActiveFilters(component, available, active)).toBe(false);
  });

  it('ignores active filters that are not currently available', () => {
    const onlyComponent = [filterByKey('component')];
    // `community` is toggled on but not available, so it imposes no constraint.
    const active = {community: true, component: true};
    expect(matchesActiveFilters(component, onlyComponent, active)).toBe(true);
  });
});
