import React from 'react';
import clsx from 'clsx';

import {IStepState} from './RunMetadataProvider';
import styles from './ExecutionStateDot.module.css';

// Map IStepState to CSS module classnames
const stateClassMap: Record<IStepState, string> = {
  [IStepState.RUNNING]: styles.running || '',
  [IStepState.SUCCEEDED]: styles.succeeded || '',
  [IStepState.SKIPPED]: styles.skipped || '',
  [IStepState.FAILED]: styles.failed || '',
  [IStepState.PREPARING]: styles.preparing || '',
  [IStepState.RETRY_REQUESTED]: styles.retryRequested || '',
  [IStepState.UNKNOWN]: styles.unknown || '',
};

export const ExecutionStateDot = ({state}: {state: IStepState}) => (
  <div className={clsx(styles.dot, stateClassMap[state])} />
);
