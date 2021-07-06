import {NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import React from 'react';

export const NonIdealPipelineQueryResult: React.FunctionComponent<{
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
  if (result.__typename === 'PipelineSnapshotNotFoundError') {
    return (
      <NonIdealState
        icon={IconNames.FLOW_BRANCH}
        title="Pipeline Snapshot Not Found"
        description={result.message}
      />
    );
  }
  if (result.__typename === 'PipelineNotFoundError') {
    return (
      <NonIdealState
        icon={IconNames.FLOW_BRANCH}
        title="Pipeline Not Found"
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
