import {gql} from '@apollo/client';
import {
  Box,
  Button,
  Colors,
  Icon,
  JoinedButtons,
  Menu,
  MenuDivider,
  MenuItem,
  Popover,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {DeletionDialog} from './DeletionDialog';
import {RunGrouping} from './GroupedRunsRoot';
import {ReexecutionDialog} from './ReexecutionDialog';
import {doneStatuses, failedStatuses} from './RunStatuses';
import {RunsQueryRefetchContext} from './RunUtils';
import {TerminationDialog} from './TerminationDialog';
import {RunTableRunFragment} from './types/RunTable.types';
import {ReexecutionStrategy} from '../graphql/types';
import {AnchorButton} from '../ui/AnchorButton';

interface Props {
  group: RunGrouping;
}

export const RunGroupingActionsMenu = React.memo(({group}: Props) => {
  const {refetch} = React.useContext(RunsQueryRefetchContext);
  const [visibleDialog, setVisibleDialog] = React.useState<
    'none' | 'terminate' | 'delete' | 'config' | 'tags' | 'metrics'
  >('none');

  const {hasTerminatePermission, hasDeletePermission} = group.runs[0]!;

  const closeDialogs = () => {
    setVisibleDialog('none');
  };

  const onComplete = () => {
    refetch();
  };

  const isFinished = group.runs.every((run) => doneStatuses.has(run.status));

  return (
    <>
      <JoinedButtons>
        <AnchorButton to={`/runs/grouped/${group.key}`}>View details</AnchorButton>
        <Popover
          content={
            <Menu>
              <MenuItem
                tagName="button"
                text={
                  <div style={{display: 'contents'}}>
                    View all tags
                    <Box
                      flex={{
                        justifyContent: 'center',
                        alignItems: 'center',
                        display: 'inline-flex',
                      }}
                      padding={{horizontal: 8}}
                    >
                      <SlashShortcut>t</SlashShortcut>
                    </Box>
                  </div>
                }
                icon="tag"
                onClick={() => setVisibleDialog('tags')}
              />

              {isFinished || !hasTerminatePermission ? null : (
                <MenuItem
                  tagName="button"
                  icon="cancel"
                  text="Terminate"
                  onClick={() => setVisibleDialog('terminate')}
                />
              )}
              <MenuDivider />
              {hasDeletePermission ? (
                <MenuItem
                  tagName="button"
                  icon="delete"
                  text="Delete"
                  intent="danger"
                  onClick={() => setVisibleDialog('delete')}
                />
              ) : null}
            </Menu>
          }
          position="bottom-right"
        >
          <Button icon={<Icon name="expand_more" />} />
        </Popover>
      </JoinedButtons>
      {hasTerminatePermission ? (
        <TerminationDialog
          isOpen={visibleDialog === 'terminate'}
          onClose={closeDialogs}
          onComplete={onComplete}
          selectedRuns={Object.fromEntries(group.runs.map((r) => [r.id, r.canTerminate]))}
        />
      ) : null}
      {hasDeletePermission ? (
        <DeletionDialog
          isOpen={visibleDialog === 'delete'}
          onClose={closeDialogs}
          onComplete={onComplete}
          onTerminateInstead={() => setVisibleDialog('terminate')}
          selectedRuns={Object.fromEntries(group.runs.map((r) => [r.id, r.canTerminate]))}
        />
      ) : null}
    </>
  );
});

interface RunBulkActionsMenuProps {
  selected: RunTableRunFragment[];
  clearSelection: () => void;
}

export const RunBulkActionsMenu = React.memo((props: RunBulkActionsMenuProps) => {
  const {selected, clearSelection} = props;
  const {refetch} = React.useContext(RunsQueryRefetchContext);

  const [visibleDialog, setVisibleDialog] = React.useState<
    'none' | 'terminate' | 'delete' | 'reexecute-from-failure' | 'reexecute'
  >('none');

  const canTerminateAny = React.useMemo(() => {
    return selected.some((run) => run.hasTerminatePermission);
  }, [selected]);

  const canDeleteAny = React.useMemo(() => {
    return selected.some((run) => run.hasTerminatePermission);
  }, [selected]);

  const canReexecuteAny = React.useMemo(() => {
    return selected.some((run) => run.hasReExecutePermission);
  }, [selected]);

  const disabled = !canTerminateAny && !canDeleteAny;

  const terminatableRuns = selected.filter(
    (r) => !doneStatuses.has(r?.status) && r.hasTerminatePermission,
  );
  const terminateableIDs = terminatableRuns.map((r) => r.id);
  const terminateableMap = terminatableRuns.reduce(
    (accum, run) => {
      accum[run.id] = run.canTerminate;
      return accum;
    },
    {} as Record<string, boolean>,
  );

  const deleteableIDs = selected.map((run) => run.id);
  const deletionMap = selected.reduce(
    (accum, run) => {
      accum[run.id] = run.canTerminate;
      return accum;
    },
    {} as Record<string, boolean>,
  );

  const reexecuteFromFailureRuns = selected.filter(
    (r) => failedStatuses.has(r?.status) && r.hasReExecutePermission,
  );
  const reexecuteFromFailureMap = reexecuteFromFailureRuns.reduce(
    (accum, run) => {
      accum[run.id] = run.id;
      return accum;
    },
    {} as Record<string, string>,
  );

  const reexecutableRuns = selected.filter(
    (r) => doneStatuses.has(r?.status) && r.hasReExecutePermission,
  );
  const reexecutableMap = reexecutableRuns.reduce(
    (accum, run) => {
      accum[run.id] = run.id;
      return accum;
    },
    {} as Record<string, string>,
  );

  const closeDialogs = () => {
    setVisibleDialog('none');
  };

  const onComplete = () => {
    clearSelection();
    refetch();
  };

  return (
    <>
      <Popover
        disabled={disabled || selected.length === 0}
        content={
          <Menu>
            {canTerminateAny ? (
              <MenuItem
                icon="cancel"
                text={`Terminate ${terminateableIDs.length} ${
                  terminateableIDs.length === 1 ? 'run' : 'runs'
                }`}
                disabled={terminateableIDs.length === 0}
                onClick={() => {
                  setVisibleDialog('terminate');
                }}
              />
            ) : null}
            {canDeleteAny ? (
              <MenuItem
                icon="delete"
                intent="danger"
                text={`Delete ${deleteableIDs.length} ${
                  deleteableIDs.length === 1 ? 'run' : 'runs'
                }`}
                disabled={deleteableIDs.length === 0}
                onClick={() => {
                  setVisibleDialog('delete');
                }}
              />
            ) : null}
            {canReexecuteAny ? (
              <>
                <MenuItem
                  icon="refresh"
                  text={`Re-execute ${reexecutableRuns.length} ${
                    reexecutableRuns.length === 1 ? 'run' : 'runs'
                  }`}
                  disabled={reexecutableRuns.length === 0}
                  onClick={() => {
                    setVisibleDialog('reexecute');
                  }}
                />
                <MenuItem
                  icon="refresh"
                  text={`Re-execute ${reexecuteFromFailureRuns.length} ${
                    reexecuteFromFailureRuns.length === 1 ? 'run' : 'runs'
                  } from failure`}
                  disabled={reexecuteFromFailureRuns.length === 0}
                  onClick={() => {
                    setVisibleDialog('reexecute-from-failure');
                  }}
                />
              </>
            ) : null}
          </Menu>
        }
        position="bottom-right"
      >
        <Button
          disabled={disabled || selected.length === 0}
          rightIcon={<Icon name="expand_more" />}
          intent="primary"
        >
          Actions
        </Button>
      </Popover>
      <TerminationDialog
        isOpen={visibleDialog === 'terminate'}
        onClose={closeDialogs}
        onComplete={onComplete}
        selectedRuns={terminateableMap}
      />
      <DeletionDialog
        isOpen={visibleDialog === 'delete'}
        onClose={closeDialogs}
        onComplete={onComplete}
        onTerminateInstead={() => setVisibleDialog('terminate')}
        selectedRuns={deletionMap}
      />
      <ReexecutionDialog
        isOpen={visibleDialog === 'reexecute-from-failure'}
        onClose={closeDialogs}
        onComplete={onComplete}
        selectedRuns={reexecuteFromFailureMap}
        reexecutionStrategy={ReexecutionStrategy.FROM_FAILURE}
      />
      <ReexecutionDialog
        isOpen={visibleDialog === 'reexecute'}
        onClose={closeDialogs}
        onComplete={onComplete}
        selectedRuns={reexecutableMap}
        reexecutionStrategy={ReexecutionStrategy.ALL_STEPS}
      />
    </>
  );
});

const OPEN_LAUNCHPAD_UNKNOWN =
  'Launchpad is unavailable because the pipeline is not present in the current repository.';

// Avoid fetching envYaml and parentPipelineSnapshotId on load in Runs page, they're slow.
export const PIPELINE_ENVIRONMENT_QUERY = gql`
  query PipelineEnvironmentQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        pipelineName
        pipelineSnapshotId
        runConfigYaml
        pipelineName
        parentPipelineSnapshotId
        repositoryOrigin {
          id
          repositoryName
          repositoryLocationName
        }
      }
    }
  }
`;

const SlashShortcut = styled.div`
  border-radius: 4px;
  padding: 0px 6px;
  background: ${Colors.backgroundLight()};
  color: ${Colors.textLight()};
`;

const LinkNoUnderline = styled(Link)`
  text-decoration: none !important;
`;
