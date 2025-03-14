import ComponentHeader from '@/app/components/ComponentHeader';
import {Package} from '@/util/types';
import Link from 'next/link';

import styles from './css/PackageDetails.module.css';

interface Props {
  pkg: Package;
}

export default function PackageDetails({pkg}: Props) {
  return (
    <div className={styles.container}>
      {pkg.componentTypes.map((component) => (
        <Link
          href={`/packages/${pkg.name}/${component.name}`}
          key={component.name}
          className={styles.componentItem}
        >
          <ComponentHeader config={component} descriptionStyle="truncated" />
        </Link>
      ))}
    </div>
  );
}
