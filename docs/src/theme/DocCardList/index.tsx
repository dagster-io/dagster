import React, {type ReactNode} from 'react';
import clsx from 'clsx';
import {useCurrentSidebarCategory, filterDocCardListItems} from '@docusaurus/plugin-content-docs/client';
import BrowserOnly from '@docusaurus/BrowserOnly';
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

  // The `DocCardList` has been customized to filter cards with `href === window.location.pathname`.
  //
  // The `window.location` is only available in the browser, and as Docusaurus is server-side
  // rendered we have to wrap this component in `BrowserOnly`. For more information see:
  //
  // https://github.com/facebook/docusaurus/blob/67924ca9795c4cd0399c752b4345f515bcedcaf6/website/docs/advanced/ssg.mdx#browseronly-browseronly

  return (
    <section className={clsx('row', className)}>
      <BrowserOnly>
        {() => {
          return filteredItems
            .filter((item) => item.href !== window.location.pathname)
            .map((item, index) => (
              <article key={index} className="col col--6 margin-bottom--lg">
                <DocCard item={item} />
              </article>
            ));
        }}
      </BrowserOnly>
    </section>
  );
}
