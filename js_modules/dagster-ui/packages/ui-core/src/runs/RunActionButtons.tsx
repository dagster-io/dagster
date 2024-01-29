import {Box, Button, Group, Icon} from '@dagster-io/ui-components';
import {useCallback, useState} from 'react';

import {IRunMetadataDict, IStepState} from './RunMetadataProvider';
import {doneStatuses, failedStatuses} from './RunStatuses';
import {DagsterTag} from './RunTag';
import {getReexecutionParamsForSelection} from './RunUtils';
import {StepSelection} from './StepSelection';
import {TerminationDialog, TerminationDialogResult} from './TerminationDialog';
import {RunFragment, RunPageFragment} from './types/RunFragments.types';
import {useJobAvailabilityErrorForRun} from './useJobAvailabilityErrorForRun';
import {useJobReexecution} from './useJobReExecution';
import {showSharedToaster} from '../app/DomUtils';
import {GraphQueryItem, filterByQuery} from '../app/GraphQueryImpl';
import {DEFAULT_DISABLED_REASON} from '../app/Permissions';
import {ReexecutionStrategy} from '../graphql/types';
import {LaunchButtonConfiguration, LaunchButtonDropdown} from '../launchpad/LaunchButton';
import {useRepositoryForRunWithParentSnapshot} from '../workspace/useRepositoryForRun';

interface RunActionButtonsProps {
  run: RunPageFragment;
  selection: StepSelection;
  graph: GraphQueryItem[];
  metadata: IRunMetadataDict;
}

export const CancelRunButton = ({run}: {run: RunFragment}) => {
  const {id: runId, canTerminate} = run;
  const [showDialog, setShowDialog] = useState<boolean>(false);
  const closeDialog = useCallback(() => setShowDialog(false), []);

  const onComplete = useCallback(
    async (result: TerminationDialogResult) => {
      const {errors} = result;
      const error = runId && errors[runId];
      if (error && 'message' in error) {
        await showSharedToaster({
          message: error.message,
          icon: 'error',
          intent: 'danger',
        });
      }
    },
    [runId],
  );

  if (!runId) {
    return null;
  }

  return (
    <>
      <Button
        icon={<Icon name="cancel" />}
        intent="danger"
        disabled={showDialog}
        onClick={() => setShowDialog(true)}
      >
        Terminate
      </Button>
      <TerminationDialog
        isOpen={showDialog}
        onClose={closeDialog}
        onComplete={onComplete}
        selectedRuns={{[runId]: canTerminate}}
      />
    </>
  );
};

function stepSelectionWithState(selection: StepSelection, metadata: IRunMetadataDict) {
  const stepStates = selection.keys.map(
    (key) => (key && metadata.steps[key]?.state) || IStepState.PREPARING,
  );

  return {
    ...selection,
    present: selection.keys.length > 0,
    failed: selection.keys.length && stepStates.includes(IStepState.FAILED),
    finished: stepStates.every((stepState) =>
      [IStepState.FAILED, IStepState.SUCCEEDED].includes(stepState),
    ),
  };
}

function stepSelectionFromRunTags(
  run: RunFragment,
  graph: GraphQueryItem[],
  metadata: IRunMetadataDict,
) {
  const tag = run.tags.find((t) => t.key === DagsterTag.StepSelection);
  if (!tag) {
    return null;
  }
  return stepSelectionWithState(
    {keys: filterByQuery(graph, tag.value).all.map((k) => k.name), query: tag.value},
    metadata,
  );
}

export const canRunAllSteps = (run: Pick<RunFragment, 'status'>) => doneStatuses.has(run.status);
export const canRunFromFailure = (run: Pick<RunFragment, 'status' | 'executionPlan'>) =>
  run.executionPlan && failedStatuses.has(run.status);

export const RunActionButtons = (props: RunActionButtonsProps) => {
  const {metadata, graph, run} = props;

  const repoMatch = useRepositoryForRunWithParentSnapshot(run);
  const jobError = useJobAvailabilityErrorForRun(run);

  const artifactsPersisted = run?.executionPlan?.artifactsPersisted;

  const selection = stepSelectionWithState(props.selection, metadata);
  const currentRunSelection = stepSelectionFromRunTags(run, graph, metadata);
  const currentRunIsFromFailure = run.tags?.some(
    (t) => t.key === DagsterTag.IsResumeRetry && t.value === 'true',
  );

  const reexecute = useJobReexecution();
  const reexecuteWithSelection = async (selection: StepSelection) => {
    if (!run || !repoMatch || !run.pipelineSnapshotId) {
      return;
    }
    const executionParams = getReexecutionParamsForSelection({
      run,
      selection,
      repositoryLocationName: repoMatch.match.repositoryLocation.name,
      repositoryName: repoMatch.match.repository.name,
    });
    await reexecute(run, executionParams);
  };

  const full: LaunchButtonConfiguration = {
    icon: 'cached',
    scope: '*',
    title: 'All steps in root run',
    tooltip: 'Re-execute the pipeline run from scratch',
    disabled: !canRunAllSteps(run),
    onClick: () => reexecute(run, ReexecutionStrategy.ALL_STEPS),
  };

  const same: LaunchButtonConfiguration = {
    icon: 'linear_scale',
    scope: currentRunSelection?.query || '*',
    title: 'Same steps',
    disabled: !currentRunSelection || !(currentRunSelection.finished || currentRunSelection.failed),
    tooltip: (
      <div>
        {!currentRunSelection || !currentRunSelection.present
          ? 'Re-executes the same step subset used for this run if one was present.'
          : !currentRunSelection.finished
          ? 'Wait for all of the steps to finish to re-execute the same subset.'
          : 'Re-execute the same step subset used for this run:'}
        <StepSelectionDescription selection={currentRunSelection} />
      </div>
    ),
    onClick: () => reexecuteWithSelection(currentRunSelection!),
  };

  const selected: LaunchButtonConfiguration = {
    icon: 'op',
    scope: selection.query,
    title: selection.keys.length > 1 ? 'Selected steps' : 'Selected step',
    disabled: !selection.present || !(selection.finished || selection.failed),
    tooltip: (
      <div>
        {!selection.present
          ? 'Select a step or type a step subset to re-execute.'
          : !selection.finished
          ? 'Wait for the steps to finish to re-execute them.'
          : 'Re-execute the selected steps with existing configuration:'}
        <StepSelectionDescription selection={selection} />
      </div>
    ),
    onClick: () => reexecuteWithSelection(selection),
  };

  const fromSelected: LaunchButtonConfiguration = {
    icon: 'arrow_forward',
    title: 'From selected',
    disabled: !canRunAllSteps(run) || selection.keys.length !== 1,
    tooltip: 'Re-execute the pipeline downstream from the selected steps',
    onClick: async () => {
      if (!run.executionPlan) {
        console.warn('Run execution plan must be present to launch from-selected execution');
        return Promise.resolve();
      }
      const selectionAndDownstreamQuery = selection.keys.map((k) => `${k}*`).join(',');
      const selectionKeys = filterByQuery(graph, selectionAndDownstreamQuery).all.map(
        (node) => node.name,
      );

      await reexecuteWithSelection({
        keys: selectionKeys,
        query: selectionAndDownstreamQuery,
      });
    },
  };

  const fromFailureEnabled = canRunFromFailure(run);

  const fromFailure: LaunchButtonConfiguration = {
    icon: 'arrow_forward',
    title: 'From failure',
    disabled: !fromFailureEnabled,
    tooltip: !fromFailureEnabled
      ? 'Retry is only enabled when the pipeline has failed.'
      : 'Retry the pipeline run, skipping steps that completed successfully',
    onClick: () => reexecute(run, ReexecutionStrategy.FROM_FAILURE),
  };

  if (!artifactsPersisted) {
    [selected, same, fromFailure, fromSelected].forEach((option) => {
      option.disabled = true;
      option.title =
        'Retry and re-execute are only enabled on persistent storage. Try rerunning with a different storage configuration.';
    });
  }

  const options = [full, same, selected, fromSelected, fromFailure];
  const preferredRerun = selection.present
    ? selected
    : fromFailureEnabled && currentRunIsFromFailure
    ? fromFailure
    : currentRunSelection?.present
    ? same
    : null;

  const primary = artifactsPersisted && preferredRerun ? preferredRerun : full;

  const tooltip = () => {
    if (jobError?.tooltip) {
      return jobError?.tooltip;
    }
    return run.hasReExecutePermission ? undefined : DEFAULT_DISABLED_REASON;
  };

  return (
    <Group direction="row" spacing={8}>
      <Box flex={{direction: 'row'}}>
        <LaunchButtonDropdown
          runCount={1}
          primary={primary}
          options={options}
          title={
            primary.scope === '*'
              ? `Re-execute all (*)`
              : primary.scope
              ? `Re-execute (${primary.scope})`
              : `Re-execute ${primary.title}`
          }
          tooltip={tooltip()}
          icon={jobError?.icon}
          disabled={jobError?.disabled || !run.hasReExecutePermission}
        />
      </Box>
      {!doneStatuses.has(run.status) ? <CancelRunButton run={run} /> : null}
    </Group>
  );
};

const StepSelectionDescription = ({selection}: {selection: StepSelection | null}) => (
  <div style={{paddingLeft: '10px'}}>
    {(selection?.keys || []).map((step) => (
      <span key={step} style={{display: 'block'}}>{`* ${step}`}</span>
    ))}
  </div>
);
