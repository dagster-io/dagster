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
    const doc = useDocById(item.docId ?? undefined);
    description = item.description ?? doc?.description;
  }

  const LinkComponent = Link as any; //Type assertion to bypass linting error

  return (
    <LinkComponent
      href={href}
      {...props}
      className={clsx('card', styles.cardContainer)}
    >
      {logo && (
            <img
              className={styles.cardLogo}
              src={useBaseUrl(logo)}
            />
        )}
        <div>
          <div className={styles.cardTitleWrapper}>
            <Heading as="h2" className={styles.cardTitle} title={title}>
              {title}
            </Heading>
            {community && (
              <span className={styles.cardTags}>Community</span>
            )}
          </div>
          {description && (
            <p className={styles.cardDescription} title={description}>
              {description}
            </p>
          )}
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
