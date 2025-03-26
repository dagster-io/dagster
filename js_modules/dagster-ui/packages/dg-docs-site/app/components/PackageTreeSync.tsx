'use client';

import PackageTree from '@dagster-io/dg-docs-components/PackageTree';
import {Contents} from '@dagster-io/dg-docs-components/types';

import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {HTMLProps} from 'react';

const renderLink = (props: HTMLProps<HTMLAnchorElement>) => <Link {...props} href={props.href!} />;

export default function PackageTreeSync({contents}: {contents: Contents | null}) {
  const pathname = usePathname();
  return <PackageTree contents={contents} pathname={pathname} renderLink={renderLink} />;
}
