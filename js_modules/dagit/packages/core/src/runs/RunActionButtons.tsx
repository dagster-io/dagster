import * as React from 'react';

import {SharedToaster} from '../app/DomUtils';
import {filterByQuery, GraphQueryItem} from '../app/GraphQueryImpl';
import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';
import {LaunchButtonConfiguration, LaunchButtonDropdown} from '../launchpad/LaunchButton';
import {RunStatus} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
import {Group} from '../ui/Group';
import {IconName, IconWIP} from '../ui/Icon';
import {buildRepoPath} from '../workspace/buildRepoAddress';
import {useRepositoryForRun} from '../workspace/useRepositoryForRun';

import {IRunMetadataDict, IStepState} from './RunMetadataProvider';
import {doneStatuses} from './RunStatuses';
import {DagsterTag} from './RunTag';
import {ReExecutionStyle} from './RunUtils';
import {StepSelection} from './StepSelection';
import {TerminationDialog, TerminationState} from './TerminationDialog';
import {RunFragment} from './types/RunFragment';

interface RunActionButtonsProps {
  run: RunFragment;
  selection: StepSelection;
  graph: GraphQueryItem[];
  metadata: IRunMetadataDict;
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
          intent: 'danger',
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
        <ButtonWIP
          icon={<IconWIP name="cancel" />}
          intent="danger"
          disabled={showDialog}
          onClick={() => setShowDialog(true)}
        >
          Terminate
        </ButtonWIP>
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

export const RunActionButtons: React.FC<RunActionButtonsProps> = (props) => {
  const {metadata, graph, onLaunch, run} = props;
  const artifactsPersisted = run?.executionPlan?.artifactsPersisted;
  const {canLaunchPipelineReexecution} = usePermissions();
  const pipelineError = usePipelineAvailabilityErrorForRun(run);

  const selection = stepSelectionWithState(props.selection, metadata);
  const selectionOfCurrentRun = stepSelectionFromRunTags(run, graph, metadata);

  const isFinalStatus = !!doneStatuses.has(run.status);
  const isFailedWithPlan =
    run.executionPlan && (run.status === RunStatus.FAILURE || run.status === RunStatus.CANCELED);

  const full: LaunchButtonConfiguration = {
    icon: 'cached',
    scope: '*',
    title: 'All Steps in Root Run',
    tooltip: 'Re-execute the pipeline run from scratch',
    disabled: !isFinalStatus,
    onClick: () => onLaunch({type: 'all'}),
  };

  const same: LaunchButtonConfiguration = {
    icon: 'linear_scale',
    scope: selectionOfCurrentRun?.query || '*',
    title: 'Same Steps',
    disabled:
      !selectionOfCurrentRun || !(selectionOfCurrentRun.finished || selectionOfCurrentRun.failed),
    tooltip: (
      <div>
        {!selectionOfCurrentRun || !selectionOfCurrentRun.present
          ? 'Re-executes the same step subset used for this run if one was present.'
          : !selectionOfCurrentRun.finished
          ? 'Wait for all of the steps to finish to re-execute the same subset.'
          : 'Re-execute the same step subset used for this run:'}
        <StepSelectionDescription selection={selectionOfCurrentRun} />
      </div>
    ),
    onClick: () => onLaunch({type: 'selection', selection: selectionOfCurrentRun!}),
  };

  const selected: LaunchButtonConfiguration = {
    icon: 'op',
    scope: selection.query,
    title: selection.keys.length > 1 ? 'Selected Steps' : 'Selected Step',
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
    onClick: () => onLaunch({type: 'selection', selection}),
  };

  const fromSelected: LaunchButtonConfiguration = {
    icon: 'arrow_forward',
    title: 'From Selected',
    disabled: !isFinalStatus || selection.keys.length !== 1,
    tooltip: 'Re-execute the pipeline downstream from the selected steps',
    onClick: () => {
      if (!run.executionPlan) {
        console.warn('Run execution plan must be present to launch from-selected execution');
        return Promise.resolve();
      }
      const selectionAndDownstreamQuery = selection.keys.map((k) => `${k}*`).join(',');
      const selectionKeys = filterByQuery(graph, selectionAndDownstreamQuery).all.map(
        (node) => node.name,
      );

      return onLaunch({
        type: 'selection',
        selection: {
          keys: selectionKeys,
          query: selectionAndDownstreamQuery,
        },
      });
    },
  };

  const fromFailure: LaunchButtonConfiguration = {
    icon: 'arrow_forward',
    title: 'From Failure',
    disabled: !isFailedWithPlan,
    tooltip: !isFailedWithPlan
      ? 'Retry is only enabled when the pipeline has failed.'
      : 'Retry the pipeline run, skipping steps that completed successfully',
    onClick: () => onLaunch({type: 'from-failure'}),
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
    : selectionOfCurrentRun?.present
    ? same
    : null;
  const primary = artifactsPersisted && preferredRerun ? preferredRerun : full;

  const tooltip = () => {
    if (pipelineError?.tooltip) {
      return pipelineError?.tooltip;
    }
    return canLaunchPipelineReexecution ? undefined : DISABLED_MESSAGE;
  };

  return (
    <Group direction="row" spacing={8}>
      <Box flex={{direction: 'row'}}>
        <LaunchButtonDropdown
          runCount={1}
          primary={primary}
          options={options}
          title={primary.scope === '*' ? `Re-execute All (*)` : `Re-execute (${primary.scope})`}
          tooltip={tooltip()}
          icon={pipelineError?.icon}
          disabled={pipelineError?.disabled || !canLaunchPipelineReexecution}
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
      icon: 'error',
      tooltip: `"${run.pipeline.name}" could not be found.`,
      disabled: true,
    };
  }

  if (repoMatch) {
    const {type: matchType} = repoMatch;

    // The run matches the repository and active snapshot ID for the pipeline. This is the best
    // we can do, so consider it safe to run as-is.
    if (matchType === 'origin-and-snapshot') {
      return null;
    }

    // Beyond this point, we're just trying our best. Warn the user that behavior might not be what
    // they expect.

    if (matchType === 'origin-only') {
      // Only the repo is a match.
      return {
        icon: 'warning',
        tooltip: `The workspace version of "${run.pipeline.name}" may be different than the one used for the original run.`,
        disabled: false,
      };
    }

    if (matchType === 'snapshot-only') {
      // Only the snapshot ID matched, but not the repo.
      return {
        icon: 'warning',
        tooltip: (
          <Group direction="column" spacing={4}>
            <div>{`The original run loaded "${run.pipeline.name}" from a different repository.`}</div>
            {run.repositoryOrigin ? (
              <div>
                Original repository:{' '}
                <strong>
                  {run.repositoryOrigin.repositoryName}@
                  {run.repositoryOrigin.repositoryLocationName}
                </strong>
              </div>
            ) : null}
          </Group>
        ),
        disabled: false,
      };
    }

    // Only the pipeline name matched. This could be from any repo in the workspace.
    return {
      icon: 'warning',
      tooltip: `The pipeline "${run.pipeline.name}" may be a different version from the original pipeline run.`,
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
        <div>{`Load repository ${buildRepoPath(
          repoForRun,
          repoLocationForRun,
        )} and try again.`}</div>
      ) : null}
    </Group>
  );

  return {
    icon: 'error',
    tooltip,
    disabled: true,
  };
}

const StepSelectionDescription: React.FunctionComponent<{selection: StepSelection | null}> = ({
  selection,
}) => (
  <div style={{paddingLeft: '10px'}}>
    {(selection?.keys || []).map((step) => (
      <span key={step} style={{display: 'block'}}>{`* ${step}`}</span>
    ))}
  </div>
);
