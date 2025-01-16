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

function CardContainer({href, children}: {href: string; children: ReactNode}): ReactNode {
  return (
    <Link href={href} className={clsx('card padding--lg', styles.cardContainer)}>
      {children}
    </Link>
  );
}

function CategoryPills({categories}: {categories: Array<string>}): ReactNode {
  return (
    <div style={{display: 'flex', gap: '8px'}}>
      {categories.map((category, index) => (
        <span
          key={index}
          style={{
            paddingLeft: '8px',
            paddingRight: '8px',
            background: 'var(--theme-color-background-blue)',
            borderRadius: '16px',
            fontSize: '0.8rem',
            fontWeight: '400',
          }}
        >
          {category}
        </span>
      ))}
    </div>
  );
}

function CardLayout({
  href,
  logo,
  categories,
  title,
  description,
}: {
  href: string;

  title: string;
  logo?: string;
  categories: Array<string>;
  description?: string;
}): ReactNode {
  return (
    <CardContainer href={href}>
      <div style={{display: 'flex', flexDirection: 'row', gap: '12px'}}>
        <div style={{flex: '0 0 64px', display: logo ? 'block' : 'none'}}>
          <img src={useBaseUrl(logo)} style={{display: 'block', width: '64px', height: '64px'}} />
        </div>
        <div>
          <Heading as="h2" className={clsx('', styles.cardTitle)} title={title}>
            {title}
          </Heading>
          {description && (
            <p className={clsx(styles.cardDescription)} title={description}>
              {description}
            </p>
          )}
          <CategoryPills categories={categories} />
        </div>
      </div>
    </CardContainer>
  );
}

function CardCategory({item}: {item: PropSidebarItemCategory}): ReactNode {
  const href = findFirstSidebarItemLink(item);
  const categoryItemsPlural = useCategoryItemsPlural();

  // Unexpected: categories that don't have a link have been filtered upfront
  if (!href) {
    return null;
  }

  const logo: string | null = item?.customProps?.logo || null;
  const categories: Array<string> = item?.customProps?.categories || [];

  return (
    <CardLayout
      href={href}
      title={item.label}
      logo={logo}
      categories={categories}
      description={item.description ?? categoryItemsPlural(item.items.length)}
    />
  );
}

function CardLink({item}: {item: PropSidebarItemLink}): ReactNode {
  // https://github.com/facebook/docusaurus/discussions/10476
  //const icon = item?.customProps?.myEmoji ?? (isInternalUrl(item.href) ? '📄️' : '🔗');
  const logo: string | null = item?.customProps?.logo || null;
  const categories: Array<string> = item?.customProps?.categories || [];
  const doc = useDocById(item.docId ?? undefined);

  return (
    <CardLayout
      href={item.href}
      logo={logo}
      categories={categories}
      title={item.label}
      description={item.description ?? doc?.description}
    />
  );
}

export default function DocCard({item}: Props): ReactNode {
  switch (item.type) {
    case 'link':
      return <CardLink item={item} />;
    case 'category':
      return <CardCategory item={item} />;
    default:
      throw new Error(`unknown item type ${JSON.stringify(item)}`);
  }
}
