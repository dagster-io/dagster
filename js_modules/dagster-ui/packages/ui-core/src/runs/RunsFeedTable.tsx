import {gql} from '@apollo/client';
import {Box, Table} from '@dagster-io/ui-components';
import * as React from 'react';

import {RUN_ACTIONS_MENU_RUN_FRAGMENT} from './RunActionsMenu';
import {RunTableActionBar} from './RunTableActionBar';
import {RunTableEmptyState} from './RunTableEmptyState';
import {RunsFeedRow} from './RunsFeedRow';
import {RunFilterToken} from './RunsFilterInput';
import {RunsFeedTableEntryFragment} from './types/RunsFeedTable.types';
import {RunsFilter} from '../graphql/types';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {BACKFILL_STEP_STATUS_DIALOG_BACKFILL_FRAGMENT} from '../instance/backfill/BackfillStepStatusDialog';
import {PARTITION_SET_FOR_BACKFILL_TABLE_FRAGMENT} from '../instance/backfill/BackfillTable';

interface RunsFeedTableProps {
  entries: RunsFeedTableEntryFragment[];
  refetch: () => void;
  filter?: RunsFilter;
  onAddTag?: (token: RunFilterToken) => void;
  actionBarComponents?: React.ReactNode;
  belowActionBarComponents?: React.ReactNode;
  emptyState?: () => React.ReactNode;
}

export const RunsFeedTable = (props: RunsFeedTableProps) => {
  const {
    entries,
    refetch,
    filter,
    onAddTag,
    actionBarComponents,
    belowActionBarComponents,
    emptyState,
  } = props;
  // const runs = React.useMemo(() => groups.flatMap((g) => g.runs), [groups]);
  const entriesIds = React.useMemo(() => entries.map((r) => r.id), [entries]);

  const [{checkedIds}, {onToggleFactory, onToggleAll}] = useSelectionReducer(entriesIds);

  // const canTerminateOrDeleteAny = React.useMemo(() => {
  //   return runs.some((run) => run.hasTerminatePermission || run.hasDeletePermission);
  // }, [runs]);

  function content() {
    if (entries.length === 0) {
      const anyFilter = !!Object.keys(filter || {}).length;
      if (emptyState) {
        return <>{emptyState()}</>;
      }

      return <RunTableEmptyState anyFilter={anyFilter} />;
    }

    return (
      <Table>
        <thead>
          <tr>
            {/* {canTerminateOrDeleteAny ? (
              <th style={{width: 42, paddingTop: 0, paddingBottom: 0}}>
                <Checkbox
                  indeterminate={checkedIds.size > 0 && checkedIds.size !== runs.length}
                  checked={checkedIds.size === runs.length}
                  onChange={(e: React.FormEvent<HTMLInputElement>) => {
                    if (e.target instanceof HTMLInputElement) {
                      onToggleAll(e.target.checked);
                    }
                  }}
                />
              </th>
            ) : null} */}
            <th>Run ID</th>
            <th style={{width: 220}}>Target</th>
            <th style={{width: 220}}>Launched by</th>
            <th style={{width: 140}}>Status</th>
            <th style={{width: 150}}>Created at</th>
            <th style={{width: 120}}>Duration</th>
            <th style={{width: 52}} />
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <RunsFeedRow
              key={entry.id}
              entry={entry}
              // hasCheckboxColumn={canTerminateOrDeleteAny}
              // canTerminateOrDelete={
              //   group.runs[0]!.hasTerminatePermission || group.runs[0]!.hasDeletePermission
              // }
              onAddTag={onAddTag}
              checked={checkedIds.has(entry.id)}
              onToggleChecked={onToggleFactory(entry.id)}
              hasCheckboxColumn={false}
              canTerminateOrDelete={false}
              refetch={refetch}
            />
          ))}
        </tbody>
      </Table>
    );
  }

  const selectedFragments = entries.filter((entry) => checkedIds.has(entry.id));

  return (
    <>
      <RunTableActionBar
        sticky
        top={
          <Box
            flex={{
              direction: 'row',
              justifyContent: 'space-between',
              alignItems: 'center',
              grow: 1,
            }}
          >
            {actionBarComponents}
            {/* <RunBulkActionsMenu
              selected={selectedFragments}
              clearSelection={() => onToggleAll(false)}
            /> */}
          </Box>
        }
        bottom={belowActionBarComponents}
      />
      {content()}
    </>
  );
};

export const RUNS_FEED_TABLE_ENTRY_FRAGMENT = gql`
  fragment RunsFeedTableEntryFragment on RunsFeedEntry {
    __typename
    id
    runStatus
    creationTime
    startTime
    endTime
    tags {
      key
      value
    }
    jobName
    assetSelection {
      ... on AssetKey {
        path
      }
    }
    assetCheckSelection {
      name
      assetKey {
        path
      }
    }
    ... on Run {
      repositoryOrigin {
        id
        repositoryLocationName
        repositoryName
      }
      ...RunActionsMenuRunFragment
    }
    ... on PartitionBackfill {
      backfillStatus: status
      partitionSetName
      partitionSet {
        id
        ...PartitionSetForBackfillTableFragment
      }
      assetSelection {
        path
      }

      hasCancelPermission
      hasResumePermission
      isAssetBackfill
      numCancelable
      ...BackfillStepStatusDialogBackfillFragment
    }
  }

  ${RUN_ACTIONS_MENU_RUN_FRAGMENT}
  ${PARTITION_SET_FOR_BACKFILL_TABLE_FRAGMENT}
  ${BACKFILL_STEP_STATUS_DIALOG_BACKFILL_FRAGMENT}
`;
