import React from 'react';

import {NonIdealState} from '../ui/NonIdealState';

interface Props {
  isGraph: boolean;
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
        __typename: 'RepositoryNotFoundError';
        message: string;
      }
    | {
        __typename: 'PythonError';
        message: string;
      };
}

export const NonIdealPipelineQueryResult: React.FC<Props> = ({isGraph, result}) => {
  if (result.__typename === 'PipelineSnapshotNotFoundError') {
    return (
      <NonIdealState
        icon="error"
        title={isGraph ? 'Graph snapshot not found' : 'Pipeline snapshot not found'}
        description={result.message}
      />
    );
  }
  if (result.__typename === 'PipelineNotFoundError') {
    return (
      <NonIdealState
        icon="error"
        title={isGraph ? 'Graph not found' : 'Pipeline not found'}
        description={result.message}
      />
    );
  }
  if (result.__typename === 'RepositoryNotFoundError') {
    return (
      <NonIdealState icon="error" title={'Repository not found'} description={result.message} />
    );
  }
  if (result.__typename === 'PythonError') {
    return <NonIdealState icon="error" title="Query Error" description={result.message} />;
  }
  return <span />;
};
