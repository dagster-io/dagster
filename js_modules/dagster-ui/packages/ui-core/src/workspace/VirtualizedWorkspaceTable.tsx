import {LazyQueryExecFunction, QueryResult} from '@apollo/client';
import {Caption, Colors} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {RepoSectionHeader} from '../runs/RepoSectionHeader';
import {Row} from '../ui/VirtualizedTable';

import {RepoAddress} from './types';

export const RepoRow = ({
  repoAddress,
  height,
  start,
  expanded,
  onToggle,
  onToggleAll,
  showLocation,
  rightElement,
}: {
  repoAddress: RepoAddress;
  height: number;
  start: number;
  showLocation: boolean;
  rightElement: React.ReactNode;
  expanded: boolean;
  onToggle: (repoAddress: RepoAddress) => void;
  onToggleAll: (expanded: boolean) => void;
}) => {
  return (
    <Row $height={height} $start={start}>
      <RepoSectionHeader
        repoName={repoAddress.name}
        repoLocation={repoAddress.location}
        expanded={expanded}
        onClick={(e: React.MouseEvent) =>
          e.getModifierState('Shift') ? onToggleAll(!expanded) : onToggle(repoAddress)
        }
        showLocation={showLocation}
        rightElement={rightElement}
      />
    </Row>
  );
};

export const LoadingOrNone = ({
  queryResult,
  noneString = 'None',
}: {
  queryResult: QueryResult<any, any>;
  noneString?: React.ReactNode;
}) => {
  const {called, loading, data} = queryResult;
  return (
    <div style={{color: Colors.textLight()}}>
      {!called || (loading && !data) ? 'Loading' : noneString}
    </div>
  );
};

export const CaptionText = ({children}: {children: React.ReactNode}) => {
  return (
    <CaptionTextContainer>
      <Caption>{children}</Caption>
    </CaptionTextContainer>
  );
};

const CaptionTextContainer = styled.div`
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;

  ${Caption} {
    color: ${Colors.textLight()};
    white-space: nowrap;
  }
`;

const JOB_QUERY_DELAY = 100;

export const useDelayedRowQuery = (lazyQueryFn: LazyQueryExecFunction<any, any>) => {
  React.useEffect(() => {
    const timer = setTimeout(() => {
      lazyQueryFn();
    }, JOB_QUERY_DELAY);

    return () => clearTimeout(timer);
  }, [lazyQueryFn]);
};
