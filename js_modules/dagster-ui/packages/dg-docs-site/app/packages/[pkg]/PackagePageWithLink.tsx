'use client';

import PackagePageDetails from '@dagster-io/dg-docs-components/PackagePageDetails';
import {DocsLinkProps, Package} from '@dagster-io/dg-docs-components/types';
import Link from 'next/link';

const renderLink = ({key, href, ...rest}: DocsLinkProps) => (
  <Link key={key} href={href!} {...rest} />
);

export default function PackagePageWithLink({pkgConfig}: {pkgConfig: Package}) {
  return <PackagePageDetails pkg={pkgConfig} renderLink={renderLink} />;
}
