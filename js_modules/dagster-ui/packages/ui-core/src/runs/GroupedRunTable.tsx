import {Box, Checkbox, Table} from '@dagster-io/ui-components';
import * as React from 'react';

import {GroupedRunRow} from './GroupedRunRow';
import {RunGrouping} from './GroupedRunsRoot';
import {RunBulkActionsMenu} from './RunActionsMenu';
import {RunTableActionBar} from './RunTableActionBar';
import {RunTableEmptyState} from './RunTableEmptyState';
import {RunFilterToken} from './RunsFilterInput';
import {RunsFilter} from '../graphql/types';
import {useSelectionReducer} from '../hooks/useSelectionReducer';

interface GroupedRunTableProps {
  groups: RunGrouping[];
  filter?: RunsFilter;
  onAddTag?: (token: RunFilterToken) => void;
  actionBarComponents?: React.ReactNode;
  belowActionBarComponents?: React.ReactNode;
  emptyState?: () => React.ReactNode;
}

export const GroupedRunTable = (props: GroupedRunTableProps) => {
  const {groups, filter, onAddTag, actionBarComponents, belowActionBarComponents, emptyState} =
    props;
  const runs = React.useMemo(() => groups.flatMap((g) => g.runs), [groups]);
  const allIds = React.useMemo(() => runs.map((r) => r.id), [runs]);

  const [{checkedIds}, {onToggleFactory, onToggleAll}] = useSelectionReducer(allIds);

  const canTerminateOrDeleteAny = React.useMemo(() => {
    return runs.some((run) => run.hasTerminatePermission || run.hasDeletePermission);
  }, [runs]);

  function content() {
    if (runs.length === 0) {
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
            {canTerminateOrDeleteAny ? (
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
            ) : null}
            <th>Run Request ID</th>
            <th style={{width: 150}}>Created at</th>
            <th style={{width: 180}}>Launched by</th>
            <th style={{width: 120}}>Status</th>
            <th style={{width: 120}}>Duration</th>
            <th style={{width: 52}} />
          </tr>
        </thead>
        <tbody>
          {groups.map((group) => (
            <GroupedRunRow
              key={group.key}
              group={group}
              hasCheckboxColumn={canTerminateOrDeleteAny}
              canTerminateOrDelete={
                group.runs[0]!.hasTerminatePermission || group.runs[0]!.hasDeletePermission
              }
              onAddTag={onAddTag}
              checked={checkedIds.has(group.key)}
              onToggleChecked={onToggleFactory(group.key)}
            />
          ))}
        </tbody>
      </Table>
    );
  }

  const selectedFragments = runs.filter((run) => checkedIds.has(run.id));

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
            <RunBulkActionsMenu
              selected={selectedFragments}
              clearSelection={() => onToggleAll(false)}
            />
          </Box>
        }
        bottom={belowActionBarComponents}
      />
      {content()}
    </>
  );
};
