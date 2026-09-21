import {Tooltip} from '@dagster-io/ui-components';

import styles from './css/LegacyPipelineTag.module.css';

export const LegacyPipelineTag = () => (
  <Tooltip content="Legacy pipeline" placement="top">
    <div className={styles.legacyTag}>Legacy</div>
  </Tooltip>
);
