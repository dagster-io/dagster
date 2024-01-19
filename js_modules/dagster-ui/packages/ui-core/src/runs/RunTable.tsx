import {gql} from '@apollo/client';
import {
  Box,
  Checkbox,
  Icon,
  NonIdealState,
  ProductTour,
  ProductTourPosition,
  Table,
} from '@dagster-io/ui-components';
import * as React from 'react';

import {RunBulkActionsMenu} from './RunActionsMenu';
import {RunRow} from './RunRow';
import {RUN_TIME_FRAGMENT} from './RunUtils';
import {RunFilterToken} from './RunsFilterInput';
import ShowAndHideTagsMP4 from './ShowAndHideRunTags.mp4';
import {RunTableRunFragment} from './types/RunTable.types';
import {RunsFilter} from '../graphql/types';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {AnchorButton} from '../ui/AnchorButton';

interface RunTableProps {
  runs: RunTableRunFragment[];
  filter?: RunsFilter;
  onAddTag?: (token: RunFilterToken) => void;
  actionBarComponents?: React.ReactNode;
  highlightedIds?: string[];
  additionalColumnHeaders?: React.ReactNode[];
  additionalColumnsForRow?: (run: RunTableRunFragment) => React.ReactNode[];
  belowActionBarComponents?: React.ReactNode;
  hideCreatedBy?: boolean;
  additionalActionsForRun?: (run: RunTableRunFragment) => JSX.Element[];
  emptyState?: () => React.ReactNode;
}

export const RunTable = (props: RunTableProps) => {
  const {
    runs,
    filter,
    onAddTag,
    highlightedIds,
    actionBarComponents,
    belowActionBarComponents,
    hideCreatedBy,
    emptyState,
  } = props;
  const allIds = runs.map((r) => r.id);

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

      return (
        <div>
          <Box margin={{vertical: 32}}>
            {anyFilter ? (
              <NonIdealState
                icon="run"
                title="No matching runs"
                description="No runs were found for this filter."
              />
            ) : (
              <NonIdealState
                icon="run"
                title="No runs found"
                description={
                  <Box flex={{direction: 'column', gap: 12}}>
                    <div>You have not launched any runs yet.</div>
                    <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
                      <AnchorButton icon={<Icon name="add_circle" />} to="/overview/jobs">
                        Launch a run
                      </AnchorButton>
                      <span>or</span>
                      <AnchorButton icon={<Icon name="materialization" />} to="/asset-groups">
                        Materialize an asset
                      </AnchorButton>
                    </Box>
                  </Box>
                }
              />
            )}
          </Box>
        </div>
      );
    } else {
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
              <th style={{width: 90}}>Run ID</th>
              <th style={{width: 180}}>Created date</th>
              <th>
                <TargetHeader />
              </th>
              {hideCreatedBy ? null : <th style={{width: 160}}>Launched by</th>}
              <th style={{width: 120}}>Status</th>
              <th style={{width: 190}}>Duration</th>
              {props.additionalColumnHeaders}
              <th style={{width: 52}} />
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <RunRow
                canTerminateOrDelete={run.hasTerminatePermission || run.hasDeletePermission}
                run={run}
                key={run.id}
                onAddTag={onAddTag}
                checked={checkedIds.has(run.id)}
                additionalColumns={props.additionalColumnsForRow?.(run)}
                additionalActionsForRun={props.additionalActionsForRun}
                onToggleChecked={onToggleFactory(run.id)}
                isHighlighted={highlightedIds && highlightedIds.includes(run.id)}
                hideCreatedBy={hideCreatedBy}
              />
            ))}
          </tbody>
        </Table>
      );
    }
  }

  const selectedFragments = runs.filter((run) => checkedIds.has(run.id));

  return (
    <>
      <ActionBar
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

export const RUN_TAGS_FRAGMENT = gql`
  fragment RunTagsFragment on PipelineTag {
    key
    value
  }
`;

export const RUN_TABLE_RUN_FRAGMENT = gql`
  fragment RunTableRunFragment on Run {
    id
    status
    stepKeysToExecute
    canTerminate
    hasReExecutePermission
    hasTerminatePermission
    hasDeletePermission
    mode
    rootRunId
    parentRunId
    pipelineSnapshotId
    pipelineName
    repositoryOrigin {
      id
      repositoryName
      repositoryLocationName
    }
    solidSelection
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
    status
    tags {
      ...RunTagsFragment
    }
    ...RunTimeFragment
  }

  ${RUN_TIME_FRAGMENT}
  ${RUN_TAGS_FRAGMENT}
`;

function ActionBar({top, bottom}: {top: React.ReactNode; bottom?: React.ReactNode}) {
  return (
    <Box flex={{direction: 'column'}} padding={{vertical: 12}}>
      <Box flex={{alignItems: 'center', gap: 12}} padding={{left: 24, right: 12}}>
        {top}
      </Box>
      {bottom ? (
        <Box
          margin={{top: 12}}
          padding={{left: 24, right: 12, top: 8}}
          border="top"
          flex={{gap: 8, wrap: 'wrap'}}
        >
          {bottom}
        </Box>
      ) : null}
    </Box>
  );
}

function TargetHeader() {
  const [hideTabPinningNux, setHideTabPinningNux] = useStateWithStorage<any>(
    'RunTableTabPinningNux',
    (value) => value,
  );
  if (hideTabPinningNux) {
    return <div>Target</div>;
  }
  return (
    <ProductTour
      title="Hide and show run tags"
      description={
        <>
          You can show tags that you prefer quick access to and hide tags you don&apos;t by hovering
          over the tag and selecting the show/hide tag option.
        </>
      }
      position={ProductTourPosition.BOTTOM_RIGHT}
      video={ShowAndHideTagsMP4}
      width="616px"
      actions={{
        dismiss: () => {
          setHideTabPinningNux('1');
        },
      }}
    >
      <div>Target</div>
    </ProductTour>
  );
}
