import {NonIdealState} from '@dagster-io/ui';
import React from 'react';

import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

interface Props {
  isGraph: boolean;
  repoAddress?: RepoAddress;
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

export const NonIdealPipelineQueryResult: React.FC<Props> = ({isGraph, repoAddress, result}) => {
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
      <NonIdealState
        icon="error"
        title={`${repoAddress ? repoAddressAsHumanString(repoAddress) : 'Definitions'} not found`}
        description={result.message}
      />
    );
  }
  if (result.__typename === 'PythonError') {
    return <NonIdealState icon="error" title="Query error" description={result.message} />;
  }
  return <span />;
};
