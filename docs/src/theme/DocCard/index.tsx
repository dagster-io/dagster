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

function ExternalLinkIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 20 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      {...props}>
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M15.5 12.25V15.25C15.5 15.3881 15.3881 15.5 15.25 15.5H4.75C4.61193 15.5 4.5 15.3881 4.5 15.25V4.75C4.5 4.61193 4.61193 4.5 4.75 4.5H7.75H8.5V3H7.75H4.75C3.7835 3 3 3.7835 3 4.75V15.25C3 16.2165 3.7835 17 4.75 17H15.25C16.2165 17 17 16.2165 17 15.25V12.25V11.5H15.5V12.25ZM11 3H11.75H16.2495C16.6637 3 16.9995 3.33579 16.9995 3.75V8.25V9H15.4995V8.25V5.56066L10.5303 10.5298L10 11.0601L8.93934 9.99945L9.46967 9.46912L14.4388 4.5H11.75H11V3Z"
        fill="currentColor"
      />
    </svg>
  );
}

function CardLayout({
  item,
  className,
}: {
  item: PropSidebarItemCategory | PropSidebarItemLink;
  className?: string;
}): ReactNode {
  const label = item.label;
  const logo: string | null = (item?.customProps?.logo as string) || null;
  const community: boolean = (item?.customProps?.community as boolean) || false;
  const categoryItemsPlural = useCategoryItemsPlural();
  const doc = useDocById(item.type === 'link' ? (item.docId ?? undefined) : undefined);
  const logoUrl = useBaseUrl(logo || '');

  let href, description;
  if (item.type === 'category') {
    href = findFirstSidebarItemLink(item);
    // Add safety check to handle cases where a category might not have a valid link
    if (href === undefined) {
      href = null; // or another appropriate fallback
    }
    description = item.description ?? categoryItemsPlural(item.items.length);
  } else {
    href = item.href;
    description = item.description ?? doc?.description;
  }

  const LinkComponent = Link as any; //Type assertion to bypass linting error

  return (
    <LinkComponent href={href} className={clsx('card', styles.cardContainer, className)}>
      {logo && <img className={styles.cardLogo} src={logoUrl} />}
      <div>
        <div className={styles.cardTitleWrapper}>
          <Heading as="h2" className={styles.cardTitle} title={label}>
            {label}
          </Heading>
          {!isInternalUrl(href) && <ExternalLinkIcon />}
          {community && <span className={styles.cardTags}>Community</span>}
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
