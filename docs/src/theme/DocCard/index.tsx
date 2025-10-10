import React, {type ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import {useDocById, findFirstSidebarItemLink} from '@docusaurus/plugin-content-docs/client';
import {usePluralForm} from '@docusaurus/theme-common';
import isInternalUrl from '@docusaurus/isInternalUrl';
import {translate} from '@docusaurus/Translate';

import type {Props} from '@theme/DocCard';
import Heading from '@theme/Heading';
import type {PropSidebarItemCategory, PropSidebarItemLink} from '@docusaurus/plugin-content-docs';

import styles from './styles.module.css';
import useBaseUrl from '@docusaurus/useBaseUrl';

// TODO - text for folders
// TODO - indicator for "community supported" integration

function useCategoryItemsPlural() {
  const {selectMessage} = usePluralForm();
  return (count: number) =>
    selectMessage(
      count,
      translate(
        {
          message: '1 item|{count} items',
          id: 'theme.docs.DocCard.categoryDescription.plurals',
          description:
            'The default description for a category card in the generated index about how many items this category includes',
        },
        {count},
      ),
    );
}

function CardLayout({
  item,
  ...props
}: {
  item: PropSidebarItemCategory | PropSidebarItemLink;
} & React.ComponentPropsWithoutRef<'a'>): ReactNode {
  const title = item.label;
  const logo: string | null = (item?.customProps?.logo as string) || null;
  const community: boolean = (item?.customProps?.community as boolean) || false;
  let href, description;
  const categoryItemsPlural = useCategoryItemsPlural();
  if (item.type === 'category') {
    href = findFirstSidebarItemLink(item);
    description = item.description ?? categoryItemsPlural(item.items.length);
  } else {
    href = item.href;
    description = item.description;
  }

  const LinkComponent = Link as any; // ← Type assertion to bypass the error

  return (
    <LinkComponent
      href={href}
      {...props}
      className={clsx('card padding--lg', styles.cardContainer)}
      style={{height: '100%'}}>
      <div style={{display: 'flex', flexDirection: 'row', gap: '12px'}} className="cardContainer">
        {logo && (
          <div style={{flex: '0 0 64px'}}>
            <img
              src={useBaseUrl(logo)}
              style={{
                display: 'block',
                width: '64px',
                height: '64px',
                background: 'var(--dagster-white)',
                padding: '4px',
              }}
            />
          </div>
        )}
        <div>
          <div style={{display: 'flex', flexDirection: 'row'}}>
            <Heading as="h2" className={styles.cardTitle} title={title}>
              {title}
            </Heading>
            {community && (
              <span style={{marginLeft: 'auto'}}>
                <div className={styles.cardTags}>Community</div>
              </span>
            )}
          </div>
          {description && (
            <p className={styles.cardDescription} title={description}>
              {description}
            </p>
          )}
        </div>
      </div>
    </LinkComponent>
  );
}

export default function DocCard({item}: Props): ReactNode {
  if (item.type !== 'link' && item.type !== 'category') {
    throw new Error(`unknown item type ${JSON.stringify(item)}`);
  }
  return <CardLayout item={item} />;
}
