import {Button, IconName, Intent} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';

import {SharedToaster} from 'src/app/DomUtils';
import {filterByQuery} from 'src/app/GraphQueryImpl';
import {LaunchButtonConfiguration, LaunchButtonDropdown} from 'src/execute/LaunchButton';
import {toGraphQueryItems} from 'src/gantt/toGraphQueryItems';
import {IStepState} from 'src/runs/RunMetadataProvider';
import {doneStatuses} from 'src/runs/RunStatuses';
import {ReExecutionStyle} from 'src/runs/RunUtils';
import {StepSelection} from 'src/runs/StepSelection';
import {TerminationDialog, TerminationState} from 'src/runs/TerminationDialog';
import {RunFragment} from 'src/runs/types/RunFragment';
import {PipelineRunStatus} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {useRepositoryForRun} from 'src/workspace/useRepositoryForRun';

// Descriptions of re-execute options
export const REEXECUTE_PIPELINE_UNKNOWN =
  'Re-execute is unavailable because the pipeline is not present in the current workspace.';
const REEXECUTE_SUBSET = 'Re-run the following steps with existing configuration:';
const REEXECUTE_SUBSET_NO_SELECTION =
  'Re-execute is only enabled when steps are selected. Try selecting a step or typing a step subset to re-execute.';
const REEXECUTE_SUBSET_NOT_DONE = 'Wait for the selected steps to finish to re-execute it.';

interface RunActionButtonsProps {
  run?: RunFragment;
  runtimeStepKeys: string[];
  selection: StepSelection;
  selectionStates: IStepState[];
  artifactsPersisted: boolean;
  onLaunch: (style: ReExecutionStyle) => Promise<void>;
}

const CancelRunButton: React.FC<{run: RunFragment | undefined; isFinalStatus: boolean}> = ({
  run,
  isFinalStatus,
}) => {
  const [showDialog, setShowDialog] = React.useState<boolean>(false);
  const closeDialog = React.useCallback(() => setShowDialog(false), []);

  const onComplete = React.useCallback(
    (terminationState: TerminationState) => {
      const {errors} = terminationState;
      const error = run?.id && errors[run.id];
      if (error && 'message' in error) {
        SharedToaster.show({
          message: error.message,
          icon: 'error',
          intent: Intent.DANGER,
        });
      }
    },
    [run?.id],
  );

  if (!run) {
    return null;
  }

  return (
    <>
      {!isFinalStatus ? (
        <Button
          icon={IconNames.STOP}
          small={true}
          text="Terminate"
          intent="warning"
          disabled={showDialog}
          onClick={() => setShowDialog(true)}
        />
      ) : null}
      <TerminationDialog
        isOpen={showDialog}
        onClose={closeDialog}
        onComplete={onComplete}
        selectedRuns={{[run.id]: run.canTerminate}}
      />
    </>
  );
};

export const RunActionButtons: React.FC<RunActionButtonsProps> = ({
  selection,
  selectionStates,
  artifactsPersisted,
  onLaunch,
  run,
  runtimeStepKeys,
}) => {
  const pipelineError = usePipelineAvailabilityErrorForRun(run);

  const isSelectionPresent = selection.keys.length > 0;
  const isSelectionFinished = selectionStates.every((stepState) =>
    [IStepState.FAILED, IStepState.SUCCEEDED].includes(stepState),
  );
  const isFinalStatus = !!(run && doneStatuses.has(run.status));
  const isFailedWithPlan =
    run &&
    run.executionPlan &&
    (run.status === PipelineRunStatus.FAILURE || run.status == PipelineRunStatus.CANCELED);
  const isFailureInSelection = selection.keys.length && selectionStates.includes(IStepState.FAILED);

  const full: LaunchButtonConfiguration = {
    icon: 'repeat',
    scope: '*',
    title: 'All Steps',
    tooltip: 'Re-execute the pipeline run from scratch',
    disabled: !isFinalStatus,
    onClick: () => onLaunch({type: 'all'}),
  };

  const selected: LaunchButtonConfiguration = {
    icon: 'select',
    scope: selection.query,
    title: selection.keys.length > 1 ? 'Selected Steps' : 'Selected Step',
    disabled: !isSelectionPresent || !(isSelectionFinished || isFailureInSelection),
    tooltip: (
      <div>
        {!isSelectionPresent
          ? REEXECUTE_SUBSET_NO_SELECTION
          : !isSelectionFinished
          ? REEXECUTE_SUBSET_NOT_DONE
          : REEXECUTE_SUBSET}
        <div style={{paddingLeft: '10px'}}>
          {isSelectionPresent &&
            selection.keys.map((step) => (
              <span key={step} style={{display: 'block'}}>{`* ${step}`}</span>
            ))}
        </div>
      </div>
    ),
    onClick: () => onLaunch({type: 'selection', selection}),
  };

  const fromSelected: LaunchButtonConfiguration = {
    icon: 'inheritance',
    title: 'From Selected',
    disabled: !isFinalStatus || selection.keys.length !== 1,
    tooltip: 'Re-execute the pipeline downstream from the selected steps',
    onClick: () => {
      if (!run?.executionPlan) {
        console.warn('Run execution plan must be present to launch from-selected execution');
        return Promise.resolve();
      }
      const selectionAndDownstreamQuery = selection.keys.map((k) => `${k}*`).join(',');
      const graph = toGraphQueryItems(run.executionPlan, runtimeStepKeys);
      const graphFiltered = filterByQuery(graph, selectionAndDownstreamQuery);

      return onLaunch({
        type: 'selection',
        selection: {
          keys: graphFiltered.all.map((node) => node.name),
          query: selectionAndDownstreamQuery,
        },
      });
    },
  };

  const fromFailure: LaunchButtonConfiguration = {
    icon: 'redo',
    title: 'From Failure',
    disabled: !isFailedWithPlan,
    tooltip: !isFailedWithPlan
      ? 'Retry is only enabled when the pipeline has failed.'
      : 'Retry the pipeline run, skipping steps that completed successfully',
    onClick: () => onLaunch({type: 'from-failure'}),
  };

  if (!artifactsPersisted) {
    [selected, fromFailure, fromSelected].forEach((option) => {
      option.disabled = true;
      option.title =
        'Retry and re-execute are only enabled on persistent storage. Try rerunning with a different storage configuration.';
    });
  }

  const options = [full, selected, fromSelected, fromFailure];
  const primary = isSelectionPresent && artifactsPersisted ? selected : full;

  return (
    <Group direction="row" spacing={8}>
      <Box flex={{direction: 'row'}}>
        <LaunchButtonDropdown
          runCount={1}
          small={true}
          primary={primary}
          options={options}
          title={primary.scope === '*' ? `Re-execute All (*)` : `Re-execute (${primary.scope})`}
          tooltip={pipelineError?.tooltip}
          icon={pipelineError?.icon}
          disabled={pipelineError?.disabled}
        />
      </Box>
      <CancelRunButton run={run} isFinalStatus={isFinalStatus} />
    </Group>
  );
};

function usePipelineAvailabilityErrorForRun(
  run: RunFragment | null | undefined,
): null | {tooltip?: string | JSX.Element; icon?: IconName; disabled: boolean} {
  const repoMatch = useRepositoryForRun(run);

  // The run hasn't loaded, so no error.
  if (!run) {
    return null;
  }

  if (run?.pipeline.__typename === 'UnknownPipeline') {
    return {
      icon: IconNames.ERROR,
      tooltip: `"${run.pipeline.name}" could not be found.`,
      disabled: true,
    };
  }

  if (repoMatch) {
    const {type: matchType} = repoMatch;

    // The run matches the active snapshot ID for the pipeline, so we're safe to execute the run.
    if (matchType === 'snapshot') {
      return null;
    }

    // A repo was found, but only because the pipeline name matched. The run might not work
    // as expected.
    return {
      icon: IconNames.WARNING_SIGN,
      tooltip:
        `The pipeline "${run.pipeline.name}" in the current repository is` +
        ` a different version than the original pipeline run.`,
      disabled: false,
    };
  }

  // We could not find a repo that contained this pipeline. Inform the user that they should
  // load the missing repository.
  const repoForRun = run.repositoryOrigin?.repositoryName;
  const repoLocationForRun = run.repositoryOrigin?.repositoryLocationName;

  const tooltip = (
    <Group direction="column" spacing={8}>
      <div>{`"${run.pipeline.name}" is not available in the current workspace.`}</div>
      {repoForRun && repoLocationForRun ? (
        <div>{`Load repository ${repoForRun}@${repoLocationForRun} and try again.`}</div>
      ) : null}
    </Group>
  );

  return {
    icon: IconNames.ERROR,
    tooltip,
    disabled: true,
  };
}
