'use client';

import {DocsLinkProps, Package} from '@dagster-io/dg-docs-components/types';
import PackageDetails from '@dagster-io/dg-docs-components/PackageDetails';
import styles from './css/PackagePageDetails.module.css';
import Link from 'next/link';

const renderLink = (props: DocsLinkProps) => <Link {...props} href={props.href!} />;

export default function PackagePageDetails({pkg}: {pkg: Package}) {
  return (
    <div className={styles.container}>
      <PackageDetails pkg={pkg} renderLink={renderLink} />
    </div>
  );
}
