import React, {type ReactNode} from 'react';
import clsx from 'clsx';
import {
  useCurrentSidebarCategory,
  filterDocCardListItems,
} from '@docusaurus/plugin-content-docs/client';
import DocCard from '@theme/DocCard';
import type {Props} from '@theme/DocCardList';

function DocCardListForCurrentSidebarCategory({className}: Props) {
  const category = useCurrentSidebarCategory();
  return <DocCardList items={category.items} className={className} />;
}

export default function DocCardList(props: Props): ReactNode {
  const {items, className} = props;
  if (!items) {
    return <DocCardListForCurrentSidebarCategory {...props} />;
  }
  const filteredItems = filterDocCardListItems(items);

  // >>> BEGIN CUSTOMIZATIONS

  // Exclude link item that matches the current href (eg. Examples on the /examples` page)
  const currentHrefPath = new URL(window.location.href).pathname;
  const filteredItemsNoIndex = filteredItems.filter((item) => item.href > currentHrefPath);

  // <<< END CUSTOMIZATIONS

  return (
    <section className={clsx('row', className)}>
      {filteredItemsNoIndex.map((item, index) => (
        <article key={index} className="col col--6 margin-bottom--lg">
          <DocCard item={item} />
        </article>
      ))}
    </section>
  );
}
