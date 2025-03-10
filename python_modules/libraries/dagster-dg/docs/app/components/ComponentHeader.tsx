import {ComponentType} from '@/util/types';

import styles from './css/ComponentHeader.module.css';
import ComponentTags from '@/app/components/ComponentTags';

interface Props {
  config: ComponentType;
}

export default function ComponentHeader({config}: Props) {
  return (
    <div className={styles.container}>
      <div className={styles.heading}>
        <div className={styles.icon} />
        <div className={styles.headingContent}>
          <h1>{config.name}</h1>
          <div className={styles.description}>{config.description}</div>
        </div>
      </div>
      <ComponentTags author={config.author} tags={config.tags} />
    </div>
  );
}
