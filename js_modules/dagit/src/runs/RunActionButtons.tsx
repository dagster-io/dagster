import {Button, IconName, Intent} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {useMutation} from 'react-apollo';

import {useRepository, useRepositoryOptions} from '../DagsterRepositoryContext';
import {SharedToaster} from '../DomUtils';
import {IStepState} from '../RunMetadataProvider';
import {LaunchButtonConfiguration, LaunchButtonDropdown} from '../execute/LaunchButton';
import {PipelineRunStatus} from '../types/globalTypes';

import {CANCEL_MUTATION} from './RunUtils';

const CANCEL_TITLE = 'Terminate';

// Titles of re-execute options
const REEXECUTE_FULL_PIPELINE_TITLE = 'Full Pipeline';
const REEXECUTE_SUBSET_NO_SELECTION_TITLE = 'Step Not Selected';
const REEXECUTE_SUBSET_TITLE = `Selected Step Subset`;
const REEXECUTE_FROM_FAILURE_TITLE = 'From Failure';

// Descriptions of re-execute options
export const REEXECUTE_PIPELINE_UNKNOWN =
  'Re-execute is unavailable because the pipeline is not present in the current repository.';

const REEXECUTE_FULL_PIPELINE_DESCRIPTION = 'Re-execute the pipeline run from scratch';

const REEXECUTE_SUBSET = 'Re-run the following steps with existing configuration:';
const REEXECUTE_SUBSET_NO_SELECTION =
  'Re-execute is only enabled when steps are selected. Try selecting a step or typing a step subset to re-execute.';
const REEXECUTE_SUBSET_NO_ARTIFACTS =
  "Use a persisting storage mode such as 'filesystem' to enable step re-execution";
const REEXECUTE_SUBSET_NOT_DONE = 'Wait for the selected steps to finish to re-execute it.';

const RETRY_DESCRIPTION = 'Retry the pipeline run, skipping steps that completed successfully';
const RETRY_DISABLED = 'Retry is only enabled when the pipeline has failed.';
const RETRY_NO_ARTIFACTS =
  'Retry is only enabled on persistent storage. Try rerunning with a different storage configuration.';

interface RunActionButtonsRun {
  runId: string;
  status: PipelineRunStatus;
  pipeline: {
    __typename: string;
    name: string;
  };
  pipelineSnapshotId: string | null;
  canTerminate: boolean;
}

interface RunActionButtonsProps {
  run?: RunActionButtonsRun;
  selectedSteps: string[];
  selectedStepStates: IStepState[];
  artifactsPersisted: boolean;
  executionPlan?: {
    artifactsPersisted: boolean;
  } | null;
  onLaunch: (stepKeys?: string[], resumeRetry?: boolean) => Promise<void>;
}

const CancelRunButton: React.FunctionComponent<{
  run: RunActionButtonsRun;
}> = ({run}) => {
  const [cancel] = useMutation(CANCEL_MUTATION);
  const [inFlight, setInFlight] = React.useState(false);
  return (
    <Button
      icon={IconNames.STOP}
      small={true}
      text={CANCEL_TITLE}
      intent="warning"
      disabled={inFlight}
      onClick={async () => {
        setInFlight(true);
        const {data} = await cancel({
          variables: {runId: run.runId},
        });
        const message = data?.terminatePipelineExecution?.message;
        if (message) {
          SharedToaster.show({
            message,
            icon: 'error',
            intent: Intent.DANGER,
          });
        }
        setInFlight(false);
      }}
    />
  );
};

export const RunActionButtons: React.FunctionComponent<RunActionButtonsProps> = ({
  selectedSteps,
  artifactsPersisted,
  onLaunch,
  run,
  selectedStepStates,
  executionPlan,
}) => {
  // Run's status

  const currentRepository = useRepository();
  const {options: repositoryOptions} = useRepositoryOptions();
  const isPipelineUnknown = run?.pipeline.__typename === 'UnknownPipeline';
  const isSelectionPresent = selectedSteps && selectedSteps.length > 0;
  const isSelectionFinished = selectedStepStates.every((stepState) =>
    [IStepState.FAILED, IStepState.SUCCEEDED].includes(stepState),
  );
  const isFinalStatus =
    run?.status === PipelineRunStatus.FAILURE || run?.status === PipelineRunStatus.SUCCESS;
  const isFailedWithPlan = executionPlan && run && run.status === PipelineRunStatus.FAILURE;
  // allow subset re-execution when there is a failure in the selection
  const isFailureInSelection = selectedSteps && selectedStepStates.includes(IStepState.FAILED);

  const options: LaunchButtonConfiguration[] = [
    {
      title: REEXECUTE_FULL_PIPELINE_TITLE,
      tooltip: REEXECUTE_FULL_PIPELINE_DESCRIPTION,
      icon: 'repeat',
      disabled: isPipelineUnknown || !isFinalStatus,
      onClick: () => onLaunch(),
    },
    {
      title: isSelectionPresent ? REEXECUTE_SUBSET_TITLE : REEXECUTE_SUBSET_NO_SELECTION_TITLE,
      disabled:
        isPipelineUnknown ||
        !isSelectionPresent ||
        !(isSelectionFinished || isFailureInSelection) ||
        !artifactsPersisted,
      tooltip: (
        <div>
          {!artifactsPersisted
            ? REEXECUTE_SUBSET_NO_ARTIFACTS
            : !isSelectionPresent
            ? REEXECUTE_SUBSET_NO_SELECTION
            : !isSelectionFinished
            ? REEXECUTE_SUBSET_NOT_DONE
            : REEXECUTE_SUBSET}
          <div style={{paddingLeft: '10px'}}>
            {isSelectionPresent &&
              selectedSteps.map((step) => (
                <span key={step} style={{display: 'block'}}>{`* ${step}`}</span>
              ))}
          </div>
        </div>
      ),
      icon: 'select',
      onClick: () => onLaunch(selectedSteps),
    },
    {
      title: REEXECUTE_FROM_FAILURE_TITLE,
      icon: 'play',
      disabled: isPipelineUnknown || !isFailedWithPlan || !artifactsPersisted,
      tooltip: !artifactsPersisted
        ? RETRY_NO_ARTIFACTS
        : !isFailedWithPlan
        ? RETRY_DISABLED
        : RETRY_DESCRIPTION,
      onClick: () => onLaunch(undefined, true),
    },
  ];

  let disabled = false;
  let tooltip = undefined;
  let icon: IconName | undefined = undefined;

  const currentRepositorySnapshots = {};
  currentRepository.pipelines.forEach((pipeline) => {
    currentRepositorySnapshots[pipeline.name] = pipeline.pipelineSnapshotId;
  });

  if (run) {
    if (run.pipeline.name in currentRepositorySnapshots) {
      if (currentRepositorySnapshots[run.pipeline.name] === run.pipelineSnapshotId) {
      } else {
        icon = IconNames.WARNING_SIGN;
        tooltip = `The pipeline "${run.pipeline.name}" in the current repository is a different version than the original pipeline run.`;
      }
    } else {
      disabled = true;
      icon = IconNames.ERROR;

      const matchingRepoNames = repositoryOptions
        .map((x) => x.repository)
        .filter(
          (x) =>
            x.name !== currentRepository.name &&
            x.pipelines.map((x) => x.name).includes(run.pipeline.name),
        )
        .map((x) => x.name);

      if (matchingRepoNames.length) {
        tooltip = `"${
          run.pipeline.name
        }" is not in the current repository.  It is available in the following repositories: ${matchingRepoNames.join(
          ', ',
        )}.`;
      } else {
        tooltip = `"${run.pipeline.name}" is not in the current repository.`;
      }
    }
  }

  return (
    <>
      <LaunchButtonDropdown
        small={true}
        options={options}
        disabled={disabled}
        tooltip={tooltip}
        title="Launch Re-execution"
        icon={icon}
      />
      {run?.canTerminate && (
        <>
          <div style={{minWidth: 6}} />
          <CancelRunButton run={run} />
        </>
      )}
    </>
  );
};
