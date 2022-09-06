import {gql, useLazyQuery} from '@apollo/client';
import {Box, Caption, Colors, Tag} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import styled from 'styled-components/macro';

import {RepoSectionHeader} from '../runs/RepoSectionHeader';
import {useRepoExpansionState} from '../ui/useRepoExpansionState';

import {buildPipelineSelector} from './WorkspaceContext';
import {repoAddressAsString} from './repoAddressAsString';
import {RepoAddress} from './types';
import {SingleJobQuery, SingleJobQueryVariables} from './types/SingleJobQuery';
import {workspacePathFromAddress} from './workspacePath';

type Repository = {
  repoAddress: RepoAddress;
  jobs: string[];
};

interface Props {
  repos: Repository[];
}

type RowType =
  | {type: 'header'; repoAddress: RepoAddress; jobCount: number}
  | {type: 'job'; repoAddress: RepoAddress; name: string};

const JOBS_EXPANSION_STATE_STORAGE_KEY = 'jobs-virtualized-expansion-state';

export const VirtualizedJobTable: React.FC<Props> = ({repos}) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const {expandedKeys, onToggle} = useRepoExpansionState(JOBS_EXPANSION_STATE_STORAGE_KEY);

  const flattened: RowType[] = React.useMemo(() => {
    const flat: RowType[] = [];
    repos.forEach(({repoAddress, jobs}) => {
      flat.push({type: 'header', repoAddress, jobCount: jobs.length});
      const repoKey = repoAddressAsString(repoAddress);
      if (expandedKeys.includes(repoKey)) {
        jobs.forEach((name) => {
          flat.push({type: 'job', repoAddress, name});
        });
      }
    });
    return flat;
  }, [repos, expandedKeys]);

  const rowVirtualizer = useVirtualizer({
    count: flattened.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (ii: number) => {
      const row = flattened[ii];
      return row?.type === 'header' ? 32 : 64;
    },
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <>
      <Container ref={parentRef}>
        <Inner $totalHeight={totalHeight}>
          {items.map(({index, key, size, start}) => {
            const row: RowType = flattened[index];
            const type = row!.type;
            return type === 'header' ? (
              <RepoRow
                repoAddress={row.repoAddress}
                jobCount={row.jobCount}
                key={key}
                height={size}
                start={start}
                onToggle={onToggle}
              />
            ) : (
              <JobRow
                key={key}
                name={row.name}
                repoAddress={row.repoAddress}
                height={size}
                start={start}
              />
            );
          })}
        </Inner>
      </Container>
    </>
  );
};

const RepoRow: React.FC<{
  repoAddress: RepoAddress;
  jobCount: number;
  height: number;
  start: number;
  onToggle: (repoAddress: RepoAddress) => void;
}> = ({repoAddress, jobCount, height, start, onToggle}) => {
  return (
    <Row $height={height} $start={start}>
      <RepoSectionHeader
        repoName={repoAddress.name}
        repoLocation={repoAddress.location}
        expanded
        onClick={() => onToggle(repoAddress)}
        showLocation={false}
        rightElement={<Tag intent="primary">{jobCount}</Tag>}
      />
    </Row>
  );
};

const JOB_QUERY_DELAY = 300;

const JobRow: React.FC<{name: string; repoAddress: RepoAddress; height: number; start: number}> = ({
  name,
  repoAddress,
  height,
  start,
}) => {
  const [queryJob, {data}] = useLazyQuery<SingleJobQuery, SingleJobQueryVariables>(
    SINGLE_JOB_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      variables: {
        selector: buildPipelineSelector(repoAddress, name),
      },
    },
  );

  React.useEffect(() => {
    const timer = setTimeout(() => {
      queryJob();
    }, JOB_QUERY_DELAY);

    return () => clearTimeout(timer);
  }, [queryJob, name]);

  return (
    <Row $height={height} $start={start}>
      <Box
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        style={{display: 'grid', gridTemplateColumns: '30% 30% 30% 10%'}}
      >
        <Box
          flex={{direction: 'column', gap: 4}}
          style={{height}}
          padding={{horizontal: 24, top: 12}}
          border={{side: 'right', width: 1, color: Colors.KeylineGray}}
        >
          <div style={{whiteSpace: 'nowrap'}}>
            <a href={workspacePathFromAddress(repoAddress, `/jobs/${name}`)}>{name}</a>
          </div>
          <div>
            <Caption style={{color: Colors.Gray500}}>
              {data?.pipelineOrError.__typename === 'Pipeline'
                ? data.pipelineOrError.description
                : ''}
            </Caption>
          </div>
        </Box>
        <Box
          flex={{alignItems: 'center'}}
          padding={{horizontal: 24}}
          style={{color: Colors.Gray300}}
        >
          Loading
        </Box>
      </Box>
    </Row>
  );
};

const Container = styled.div`
  height: 100%;
  overflow: auto;
`;

type InnerProps = {
  $totalHeight: number;
};

const Inner = styled.div.attrs<InnerProps>(({$totalHeight}) => ({
  style: {
    height: `${$totalHeight}px`,
  },
}))<InnerProps>`
  position: relative;
  width: 100%;
`;

type RowProps = {$height: number; $start: number};

const Row = styled.div.attrs<RowProps>(({$height, $start}) => ({
  style: {
    height: `${$height}px`,
    transform: `translateY(${$start}px)`,
  },
}))<RowProps>`
  left: 0;
  position: absolute;
  right: 0;
  top: 0;
`;

const SINGLE_JOB_QUERY = gql`
  query SingleJobQuery($selector: PipelineSelector!) {
    pipelineOrError(params: $selector) {
      ... on Pipeline {
        id
        name
        isJob
        description
      }
    }
  }
`;
