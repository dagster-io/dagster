import {Box, Button, Icon} from '@dagster-io/ui-components';
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
import {filterRunSelectionByQuery} from '../run-selection/AntlrRunSelection';
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
        终止
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
    await reexecute.onClick(run, executionParams, false);
  };

  const full: LaunchButtonConfiguration = {
    icon: 'cached',
    scope: '*',
    title: '根运行的所有步骤',
    tooltip: '从头重新执行流水线运行。按住 Shift 点击可调整标签。',
    disabled: !canRunAllSteps(run),
    onClick: (e) => reexecute.onClick(run, ReexecutionStrategy.ALL_STEPS, e.shiftKey),
  };

  const same: LaunchButtonConfiguration = {
    icon: 'linear_scale',
    scope: currentRunSelection?.query || '*',
    title: '相同步骤',
    disabled: !currentRunSelection || !(currentRunSelection.finished || currentRunSelection.failed),
    tooltip: (
      <div>
        {!currentRunSelection || !currentRunSelection.present
          ? '如果本次运行使用了步骤子集，则重新执行相同的步骤子集。'
          : !currentRunSelection.finished
            ? '请等待所有步骤完成后再重新执行相同的步骤子集。'
            : '重新执行本次运行使用的相同步骤子集：'}
        <StepSelectionDescription selection={currentRunSelection} />
      </div>
    ),
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    onClick: () => reexecuteWithSelection(currentRunSelection!),
  };

  const selected: LaunchButtonConfiguration = {
    icon: 'op',
    scope: selection.query,
    title: selection.keys.length > 1 ? '已选步骤' : '已选步骤',
    disabled: !selection.present || !(selection.finished || selection.failed),
    tooltip: (
      <div>
        {!selection.present
          ? '选择一个步骤或输入步骤子集以重新执行。'
          : !selection.finished
            ? '请等待步骤完成后再重新执行。'
            : '使用现有配置重新执行已选步骤：'}
        <StepSelectionDescription selection={selection} />
      </div>
    ),
    onClick: () => reexecuteWithSelection(selection),
  };

  const fromSelected: LaunchButtonConfiguration = {
    icon: 'arrow_forward',
    title: '从已选开始',
    disabled: !canRunAllSteps(run) || selection.keys.length !== 1,
    tooltip: '从已选步骤开始向下游重新执行流水线。',
    onClick: async () => {
      if (!run.executionPlan) {
        console.warn('Run execution plan must be present to launch from-selected execution');
        return Promise.resolve();
      }

      const selectionForPythonFiltering = selection.keys.map((k) => `${k}*`).join(',');
      const selectionForUIFiltering = selection.keys.map((k) => `name:"${k}"+`).join(' or ');

      const selectionKeys = filterRunSelectionByQuery(graph, selectionForUIFiltering).all.map(
        (node) => node.name,
      );

      await reexecuteWithSelection({
        keys: selectionKeys,
        query: selectionForPythonFiltering,
      });
    },
  };

  const fromFailureEnabled = canRunFromFailure(run);

  const fromFailure: LaunchButtonConfiguration = {
    icon: 'arrow_forward',
    title: '从失败处继续',
    disabled: !fromFailureEnabled,
    tooltip: !fromFailureEnabled
      ? '仅当流水线失败时才能重试。'
      : '重试流水线运行，跳过已成功完成的步骤。按住 Shift 点击可调整标签。',
    onClick: (e) => reexecute.onClick(run, ReexecutionStrategy.FROM_FAILURE, e.shiftKey),
  };

  const fromAssetFailure: LaunchButtonConfiguration = {
    icon: 'arrow_forward',
    title: '从资产失败处继续',
    disabled: !fromFailureEnabled,
    tooltip: !fromFailureEnabled
      ? '仅当流水线失败时才能重试。'
      : '重试流水线运行，仅选择未成功完成的资产。按住 Shift 点击可调整标签。',
    onClick: (e) => reexecute.onClick(run, ReexecutionStrategy.FROM_ASSET_FAILURE, e.shiftKey),
  };

  if (!artifactsPersisted) {
    [selected, same, fromFailure, fromSelected].forEach((option) => {
      option.disabled = true;
      option.title =
        '重试和重新执行仅在持久化存储上可用。请尝试使用其他存储配置重新运行。';
    });
  }

  const options = [
    full,
    same,
    selected,
    fromSelected,
    fromFailure,
    run.executionPlan?.assetKeys.length ? fromAssetFailure : null,
  ].filter(Boolean) as LaunchButtonConfiguration[];
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
    <Box flex={{direction: 'row', gap: 8}}>
      <Box flex={{direction: 'row'}}>
        <LaunchButtonDropdown
          runCount={1}
          primary={primary}
          options={options}
          title={
            primary.scope === '*'
              ? `重新执行全部 (*)`
              : primary.scope
                ? `重新执行 (${primary.scope})`
                : `重新执行 ${primary.title}`
          }
          tooltip={tooltip()}
          icon={jobError?.icon}
          disabled={jobError?.disabled || !run.hasReExecutePermission}
        />
      </Box>
      {!doneStatuses.has(run.status) ? <CancelRunButton run={run} /> : null}
      {reexecute.launchpadElement}
    </Box>
  );
};

const StepSelectionDescription = ({selection}: {selection: StepSelection | null}) => (
  <div style={{paddingLeft: '10px'}}>
    {(selection?.keys || []).map((step) => (
      <span key={step} style={{display: 'block'}}>{`* ${step}`}</span>
    ))}
  </div>
);
