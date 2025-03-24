'use client';

import {DocsLinkProps, PackageDetails, Package} from '@dagster-io/dg-docs-components';

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
