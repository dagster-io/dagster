import {LazyQueryExecFunction, QueryResult} from '@apollo/client';
import {Colors} from '@dagster-io/ui';
import * as React from 'react';

import {RepoSectionHeader} from '../runs/RepoSectionHeader';
import {Row} from '../ui/VirtualizedTable';

import {RepoAddress} from './types';

export const RepoRow: React.FC<{
  repoAddress: RepoAddress;
  height: number;
  start: number;
  showLocation: boolean;
  rightElement: React.ReactNode;
  onToggle: (repoAddress: RepoAddress) => void;
}> = ({repoAddress, height, start, onToggle, showLocation, rightElement}) => {
  return (
    <Row $height={height} $start={start}>
      <RepoSectionHeader
        repoName={repoAddress.name}
        repoLocation={repoAddress.location}
        expanded
        onClick={() => onToggle(repoAddress)}
        showLocation={showLocation}
        rightElement={rightElement}
      />
    </Row>
  );
};

export const LoadingOrNone: React.FC<{queryResult: QueryResult<any, any>}> = ({queryResult}) => {
  const {called, loading, data} = queryResult;
  return (
    <div style={{color: Colors.Gray500}}>{!called || (loading && !data) ? 'Loading' : 'None'}</div>
  );
};

const JOB_QUERY_DELAY = 100;

export const useDelayedRowQuery = <Q, V>(lazyQueryFn: LazyQueryExecFunction<Q, V>) => {
  React.useEffect(() => {
    const timer = setTimeout(() => {
      lazyQueryFn();
    }, JOB_QUERY_DELAY);

    return () => clearTimeout(timer);
  }, [lazyQueryFn]);
};
