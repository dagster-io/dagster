'use client';

import {DocsLinkProps, Package} from './types';
import PackageDetails from './PackageDetails';
import styles from './css/PackagePageDetails.module.css';
import {ReactNode} from 'react';

export default function PackagePageDetails({
  pkg,
  renderLink,
}: {
  pkg: Package;
  renderLink: (props: DocsLinkProps) => ReactNode;
}) {
  return (
    <div className={styles.container}>
      <PackageDetails pkg={pkg} renderLink={renderLink} />
    </div>
  );
}
