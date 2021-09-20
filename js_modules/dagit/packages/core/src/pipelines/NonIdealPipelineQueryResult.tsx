import {NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import React from 'react';

import {useFeatureFlags} from '../app/Flags';

export const NonIdealPipelineQueryResult: React.FC<{
  result:
    | {
        __typename: 'PipelineSnapshotNotFoundError';
        message: string;
      }
    | {
        __typename: 'PipelineNotFoundError';
        message: string;
      }
    | {
        __typename: 'PythonError';
        message: string;
      };
}> = ({result}) => {
  const {flagPipelineModeTuples} = useFeatureFlags();
  if (result.__typename === 'PipelineSnapshotNotFoundError') {
    return (
      <NonIdealState
        icon={IconNames.FLOW_BRANCH}
        title={flagPipelineModeTuples ? 'Job snapshot not found' : 'Pipeline snapshot not found'}
        description={result.message}
      />
    );
  }
  if (result.__typename === 'PipelineNotFoundError') {
    return (
      <NonIdealState
        icon={IconNames.FLOW_BRANCH}
        title={flagPipelineModeTuples ? 'Job not found' : 'Pipeline not found'}
        description={result.message}
      />
    );
  }
  if (result.__typename === 'PythonError') {
    return (
      <NonIdealState icon={IconNames.ERROR} title="Query Error" description={result.message} />
    );
  }
  return <span />;
};
