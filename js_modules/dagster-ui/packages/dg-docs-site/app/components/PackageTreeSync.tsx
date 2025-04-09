'use client';

import PackageTree from '@dagster-io/dg-docs-components/PackageTree';
import {Contents} from '@dagster-io/dg-docs-components/types';

import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {HTMLProps} from 'react';

const renderLink = ({key, href, ...rest}: HTMLProps<HTMLAnchorElement>) => (
  <Link key={key} href={href!} {...rest} />
);

export default function PackageTreeSync({contents}: {contents: Contents | null}) {
  const pathname = usePathname();
  return <PackageTree contents={contents} pathname={pathname} renderLink={renderLink} />;
}
