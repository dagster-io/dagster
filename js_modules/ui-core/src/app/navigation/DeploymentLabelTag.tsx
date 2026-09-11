import {Box, Intent, Tag, Tooltip} from '@dagster-io/ui-components';
import {useContext} from 'react';

import {AppContext} from '../AppContext';
import styles from './css/DeploymentLabelTag.module.css';

const INTENTS: Intent[] = ['none', 'primary', 'success', 'warning', 'danger'];

const toIntent = (value: string | undefined): Intent =>
  INTENTS.includes(value as Intent) ? (value as Intent) : 'none';

interface Props {
  collapsed: boolean;
}

// Set via the `ui` block in dagster.yaml, so that deployments running the same
// code (production, staging) are distinguishable at a glance.
export const DeploymentLabelTag = ({collapsed}: Props) => {
  const {uiLabel, uiIntent} = useContext(AppContext);

  if (!uiLabel) {
    return null;
  }

  const intent = toIntent(uiIntent);

  // The collapsed rail is too narrow for the label, but that is exactly when the
  // deployment cue is easiest to lose, so keep a dot carrying the same color.
  if (collapsed) {
    return (
      <Box padding={{left: 8, bottom: 8}}>
        <Tooltip content={uiLabel} placement="right">
          <div className={styles.dot} data-intent={intent} />
        </Tooltip>
      </Box>
    );
  }

  return (
    <Box padding={{horizontal: 8, bottom: 8}}>
      <Tag intent={intent}>{uiLabel}</Tag>
    </Box>
  );
};
