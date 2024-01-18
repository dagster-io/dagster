import * as React from 'react';
import {gql, useQuery} from '@apollo/client';
import {useVirtualizer} from '@tanstack/react-virtual';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {
  Box,
  Button,
  ButtonLink,
  Caption,
  Dialog,
  DialogFooter,
  NonIdealState,
  Spinner,
  Tag,
  TextInput,
} from '@dagster-io/ui-components';

import {showCustomAlert} from '../../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {RunStatusTagWithID} from '../../runs/RunStatusTag';
import {DagsterTag} from '../../runs/RunTag';
import {Container, Inner, Row} from '../../ui/VirtualizedTable';
import {
  OldRunStatusAndPartitionKeyQuery,
  OldRunStatusAndPartitionKeyQueryVariables,
  OldRunStatusAndTagsFragment,
} from './types/AutomaterializeRequestedPartitionsLink.types';

interface Props {
  runIds?: string[];
  partitionKeys: string[];
  intent?: React.ComponentProps<typeof Tag>['intent'];
}

export const AutomaterializeRequestedPartitionsLink = ({runIds, partitionKeys, intent}: Props) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [queryString, setQueryString] = React.useState('');
  const queryLowercase = queryString.toLocaleLowerCase();

  const count = partitionKeys.length;

  const filteredPartitionKeys = React.useMemo(() => {
    if (queryLowercase === '') {
      return partitionKeys;
    }
    return partitionKeys.filter((partitionKey) =>
      partitionKey.toLocaleLowerCase().includes(queryLowercase),
    );
  }, [partitionKeys, queryLowercase]);

  const label = React.useMemo(() => {
    if (runIds) {
      return count === 1 ? '1 partition launched' : `${count} partitions launched`;
    }
    return count === 1 ? '1 partition' : `${count} partitions`;
  }, [count, runIds]);

  const content = () => {
    if (queryString && !filteredPartitionKeys.length) {
      return <NoMatchesEmptyState queryString={queryString} />;
    }

    return runIds ? (
      <PartitionAndRunList runIds={runIds} partitionKeys={filteredPartitionKeys} intent={intent} />
    ) : (
      <VirtualizedPartitionList partitionKeys={partitionKeys} />
    );
  };

  return (
    <>
      <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
        <Tag intent={intent}>{label}</Tag>
        <ButtonLink onClick={() => setIsOpen(true)}>
          <Caption>View details</Caption>
        </ButtonLink>
      </Box>
      <Dialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        style={{width: '750px', maxWidth: '80vw', minWidth: '500px'}}
        canOutsideClickClose
        canEscapeKeyClose
      >
        <Box
          padding={{horizontal: 24, vertical: 16}}
          flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
          border="bottom"
        >
          <div style={{fontSize: '16px'}}>
            {count === 1 ? '1 partition' : `${count} partitions`}
          </div>
          {count > 0 ? (
            <TextInput
              icon="search"
              value={queryString}
              onChange={(e) => setQueryString(e.target.value)}
              placeholder="Filter by partition…"
              style={{width: '252px'}}
            />
          ) : null}
        </Box>
        <div style={{height: '272px', overflow: 'hidden'}}>{content()}</div>
        <DialogFooter topBorder>
          <Button onClick={() => setIsOpen(false)}>Close</Button>
        </DialogFooter>
      </Dialog>
    </>
  );
};

type PartitionRunTuple = [string, OldRunStatusAndTagsFragment];

const PartitionAndRunList = ({runIds, partitionKeys}: Props) => {
  const {data, loading} = useQuery<
    OldRunStatusAndPartitionKeyQuery,
    OldRunStatusAndPartitionKeyQueryVariables
  >(RUN_STATUS_AND_PARTITION_KEY, {
    variables: {filter: {runIds}},
  });

  const runs = data?.runsOrError;

  if (!runs) {
    if (loading) {
      return (
        <Box
          padding={32}
          flex={{direction: 'row', justifyContent: 'center', gap: 12, alignItems: 'center'}}
        >
          <Spinner purpose="body-text" />
          <div>Loading partitions and runs…</div>
        </Box>
      );
    }

    return (
      <Box padding={32}>
        <NonIdealState
          icon="error"
          title="Unexpected error"
          description="An unexpected error occurred"
        />
      </Box>
    );
  }

  if (runs.__typename === 'PythonError') {
    return (
      <Box padding={32}>
        <NonIdealState
          icon="error"
          title="Python error"
          description={
            <Button
              onClick={() => {
                showCustomAlert({
                  title: 'Python error',
                  body: <PythonErrorInfo error={runs} />,
                });
              }}
            >
              View error
            </Button>
          }
        />
      </Box>
    );
  }

  if (runs.__typename === 'InvalidPipelineRunsFilterError' || !runs.results.length) {
    return (
      <Box padding={32}>
        <NonIdealState
          icon="error"
          title="Runs not found"
          description="No runs found for these partitions"
        />
      </Box>
    );
  }

  const {results} = runs;

  const runsByPartitionKey: Record<string, OldRunStatusAndTagsFragment> = Object.fromEntries(
    results
      .map((run) => {
        const {tags} = run;
        const partitionTag = tags.find(({key}) => key === DagsterTag.Partition);
        return partitionTag ? [partitionTag.value, run] : null;
      })
      .filter((tupleOrNull): tupleOrNull is PartitionRunTuple => !!tupleOrNull),
  );

  return (
    <VirtualizedPartitionList
      partitionKeys={partitionKeys}
      runsByPartitionKey={runsByPartitionKey}
    />
  );
};

const NoMatchesEmptyState = ({queryString}: {queryString: string}) => {
  return (
    <Box padding={32}>
      <NonIdealState
        icon="search"
        title="No matching partitions"
        description={
          <>
            No matching partitions for <strong>{queryString}</strong>
          </>
        }
      />
    </Box>
  );
};

interface VirtualizedListProps {
  partitionKeys: string[];
  runsByPartitionKey?: Record<string, OldRunStatusAndTagsFragment>;
}

const VirtualizedPartitionList = ({partitionKeys, runsByPartitionKey}: VirtualizedListProps) => {
  const container = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: partitionKeys.length,
    getScrollElement: () => container.current,
    estimateSize: () => 40,
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();
  const showRunTag = !!runsByPartitionKey;

  return (
    <Container ref={container} style={{padding: '8px 24px'}}>
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          const partitionKey = partitionKeys[index]!;
          const runForPartition = runsByPartitionKey ? runsByPartitionKey[partitionKey] : null;

          return (
            <Row $height={size} $start={start} key={key}>
              <Box
                style={{height: '100%'}}
                flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
                border={index < partitionKeys.length - 1 ? 'bottom' : null}
              >
                <div>{partitionKeys[index]}</div>
                {showRunTag ? (
                  <div>
                    {runForPartition ? (
                      <TagLink to={`/runs/${runForPartition.id}`}>
                        <RunStatusTagWithID
                          runId={runForPartition.id}
                          status={runForPartition.status}
                        />
                      </TagLink>
                    ) : (
                      <Tag>Run not found</Tag>
                    )}
                  </div>
                ) : null}
              </Box>
            </Row>
          );
        })}
      </Inner>
    </Container>
  );
};

export const RUN_STATUS_AND_PARTITION_KEY = gql`
  query OldRunStatusAndPartitionKey($filter: RunsFilter) {
    runsOrError(filter: $filter) {
      ... on Runs {
        results {
          id
          ...OldRunStatusAndTagsFragment
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ...PythonErrorFragment
    }
  }

  fragment OldRunStatusAndTagsFragment on Run {
    id
    status
    tags {
      key
      value
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

const TagLink = styled(Link)`
  :focus {
    outline: none;
  }
`;
