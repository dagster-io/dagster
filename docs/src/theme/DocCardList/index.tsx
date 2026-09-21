import React, {type ReactNode, useState} from 'react';
import clsx from 'clsx';
import {useCurrentSidebarCategory, filterDocCardListItems} from '@docusaurus/plugin-content-docs/client';
import {useLocation} from '@docusaurus/router';
import BrowserOnly from '@docusaurus/BrowserOnly';
import DocCard from '@theme/DocCard';
import type {Props} from '@theme/DocCardList';
import type {PropSidebarItem} from '@docusaurus/plugin-content-docs';

import styles from './styles.module.css';
import {type ActiveFilters, type FilterKey, computeAvailableFilters, matchesActiveFilters} from './filters';

function DocCardListForCurrentSidebarCategory({className}: Props) {
  const category = useCurrentSidebarCategory();
  return <DocCardList items={category.items} className={className} />;
}

// `PropSidebarItem` is a union, so both the current-page check and the React key have to narrow on
// `item.type` before reaching for a member-specific field. Only link items carry an `href`.
function itemHref(item: PropSidebarItem): string | null {
  return item.type === 'link' ? item.href : null;
}

function itemKey(item: PropSidebarItem): string {
  switch (item.type) {
    case 'link':
      return item.href;
    case 'category':
      return item.label;
    case 'html':
      return item.value;
  }
}

export default function DocCardList(props: Props): ReactNode {
  const {items, className} = props;
  const {pathname} = useLocation();
  const [activeFilters, setActiveFilters] = useState<ActiveFilters>({});

  if (!items) {
    return <DocCardListForCurrentSidebarCategory {...props} />;
  }
  const filteredItems = filterDocCardListItems(items);

  const availableFilters = computeAvailableFilters(filteredItems, pathname);

  const toggleFilter = (key: FilterKey) => setActiveFilters((current) => ({...current, [key]: !current[key]}));

  // The `DocCardList` has been customized to filter cards with `href === window.location.pathname`.
  //
  // The `window.location` is only available in the browser, and as Docusaurus is server-side
  // rendered we have to wrap this component in `BrowserOnly`. For more information see:
  //
  // https://github.com/facebook/docusaurus/blob/67924ca9795c4cd0399c752b4345f515bcedcaf6/website/docs/advanced/ssg.mdx#browseronly-browseronly

  return (
    <>
      {availableFilters.length > 0 && (
        <div className={styles.filterBar}>
          {availableFilters.map((filter) => (
            <button
              key={filter.key}
              type="button"
              className={clsx(styles.filterButton, activeFilters[filter.key] && styles.filterButtonActive)}
              aria-pressed={!!activeFilters[filter.key]}
              onClick={() => toggleFilter(filter.key)}>
              {filter.label}
            </button>
          ))}
        </div>
      )}
      <section className={clsx('card-group cols-2', styles.cardGroup, className)}>
        <BrowserOnly>
          {() => {
            return filteredItems
              .filter((item) => itemHref(item) !== window.location.pathname)
              .filter((item) => matchesActiveFilters(item, availableFilters, activeFilters))
              .map((item) => <DocCard key={itemKey(item)} item={item} />);
          }}
        </BrowserOnly>
      </section>
    </>
  );
}
