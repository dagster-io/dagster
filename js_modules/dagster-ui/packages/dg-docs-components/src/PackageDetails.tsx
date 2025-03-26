import {Fragment, ReactNode} from 'react';

import styles from './css/PackageDetails.module.css';

import ComponentHeader from './ComponentHeader';
import {DocsLinkProps, Package} from './types';

interface Props {
  pkg: Package;
  renderLink: (props: DocsLinkProps) => ReactNode;
}

export default function PackageDetails({pkg, renderLink}: Props) {
  return (
    <div className={styles.container}>
      {pkg.componentTypes.map((component) => (
        <Fragment key={component.name}>
          {renderLink({
            href: `/packages/${pkg.name}/${component.name}`,
            className: styles.componentItem,
            children: <ComponentHeader config={component} descriptionStyle="truncated" />,
          })}
        </Fragment>
      ))}
    </div>
  );
}
