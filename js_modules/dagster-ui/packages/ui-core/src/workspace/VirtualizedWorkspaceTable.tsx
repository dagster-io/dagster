import {Caption, Colors} from '@dagster-io/ui-components';
import * as React from 'react';
import {forwardRef} from 'react';
import styled from 'styled-components';

import {RepoAddress} from './types';
import {QueryResult} from '../apollo-client';
import {RepoSectionHeader} from '../runs/RepoSectionHeader';
import {Row} from '../ui/VirtualizedTable';

interface RepoRowProps {
  repoAddress: RepoAddress;
  showLocation: boolean;
  rightElement: React.ReactNode;
  expanded: boolean;
  onToggle: (repoAddress: RepoAddress) => void;
  onToggleAll: (expanded: boolean) => void;
}

interface StaticRepoRowProps extends RepoRowProps {
  height: number;
  start: number;
}

export const RepoRow = ({
  repoAddress,
  height,
  start,
  expanded,
  onToggle,
  onToggleAll,
  showLocation,
  rightElement,
}: StaticRepoRowProps) => {
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

interface DynamicRepoRowProps extends RepoRowProps {
  index: number;
}

export const DynamicRepoRow = forwardRef(
  (props: DynamicRepoRowProps, ref: React.ForwardedRef<HTMLDivElement>) => {
    const {index, repoAddress, expanded, onToggle, onToggleAll, showLocation, rightElement} = props;
    return (
      <div ref={ref} data-index={index}>
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
      </div>
    );
  },
);

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
