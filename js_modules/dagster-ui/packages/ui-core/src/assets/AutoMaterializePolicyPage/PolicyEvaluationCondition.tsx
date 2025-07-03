import {Box, Icon} from '@dagster-io/ui-components';
import clsx from 'clsx';
import * as React from 'react';

import styles from './css/PolicyEvaluationCondition.module.css';

export type ConditionType = 'group' | 'leaf';

interface Props {
  depth: number;
  icon: React.ReactNode;
  label: React.ReactNode;
  type: ConditionType;
  skipped?: boolean;
  isExpanded: boolean;
  hasChildren: boolean;
  evaluationLink?: React.ReactNode | null;
}

export const PolicyEvaluationCondition = (props: Props) => {
  const {
    depth,
    icon,
    label,
    type,
    skipped = false,
    isExpanded,
    hasChildren,
    evaluationLink,
  } = props;
  const depthLines = React.useMemo(() => {
    return new Array(depth)
      .fill(null)
      .map((_, ii) => <div key={ii} className={styles.depthLine} />);
  }, [depth]);

  return (
    <Box
      padding={{vertical: 2, horizontal: 8}}
      flex={{direction: 'row', alignItems: 'center', gap: 8}}
    >
      {depthLines}
      {hasChildren ? (
        <Icon
          name="arrow_drop_down"
          size={20}
          style={{transform: isExpanded ? 'rotate(0deg)' : 'rotate(-90deg)'}}
        />
      ) : null}
      {hasChildren ? icon : <div style={{marginLeft: 28}}>{icon}</div>}
      <div
        className={clsx(
          styles.conditionLabel,
          type === 'group' ? styles.group : null,
          skipped ? styles.skipped : null,
        )}
      >
        {label}
      </div>
      {evaluationLink ? <>[{evaluationLink}]</> : null}
    </Box>
  );
};
