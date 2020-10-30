import {ApolloClient, useMutation} from '@apollo/client';
import {NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

import {showCustomAlert} from 'src/CustomAlertProvider';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {IStepState, RunMetadataProvider} from 'src/RunMetadataProvider';
import {FirstOrSecondPanelToggle, SplitPanelContainer} from 'src/SplitPanelContainer';
import {GaantChart, GaantChartMode, queryStringToSelection} from 'src/gaant/GaantChart';
import {LogFilter, LogsProvider} from 'src/runs/LogsProvider';
import {LogsScrollingTable} from 'src/runs/LogsScrollingTable';
import {LogsToolbar} from 'src/runs/LogsToolbar';
import {RunActionButtons} from 'src/runs/RunActionButtons';
import {RunContext} from 'src/runs/RunContext';
import {RunStatusToPageAttributes} from 'src/runs/RunStatusToPageAttributes';
import {
  LAUNCH_PIPELINE_REEXECUTION_MUTATION,
  getReexecutionVariables,
  handleLaunchResult,
  ReExecutionStyle,
} from 'src/runs/RunUtils';
import {StepSelection} from 'src/runs/StepSelection';
import {getRunPageFilters} from 'src/runs/getRunPageFilters';
import {
  LaunchPipelineReexecution,
  LaunchPipelineReexecutionVariables,
} from 'src/runs/types/LaunchPipelineReexecution';
import {RunFragment} from 'src/runs/types/RunFragment';
import {
  RunPipelineRunEventFragment,
  RunPipelineRunEventFragment_ExecutionStepFailureEvent,
} from 'src/runs/types/RunPipelineRunEventFragment';
import {useWorkspaceState} from 'src/workspace/WorkspaceContext';

interface RunProps {
  client: ApolloClient<any>;
  runId: string;
  run?: RunFragment;
}

interface RunState {
  logsFilter: LogFilter;
  selection: StepSelection;
}

export const Run = (props: RunProps) => {
  const {client, run, runId} = props;
  const [logsFilter, setLogsFilter] = React.useState<LogFilter>(() =>
    getRunPageFilters(document.location.search),
  );

  const [selection, setSelection] = React.useState<StepSelection>(() => {
    const {stepQuery} = logsFilter;
    if (!stepQuery || !run?.executionPlan) {
      return {query: '*', keys: []};
    }
    return {query: stepQuery, keys: queryStringToSelection(run.executionPlan, stepQuery)};
  });

  const onShowStateDetails = (stepKey: string, logs: RunPipelineRunEventFragment[]) => {
    const errorNode = logs.find(
      (node) => node.__typename === 'ExecutionStepFailureEvent' && node.stepKey === stepKey,
    ) as RunPipelineRunEventFragment_ExecutionStepFailureEvent;

    if (errorNode) {
      showCustomAlert({
        body: <PythonErrorInfo error={errorNode} />,
      });
    }
  };

  const onSetLogsFilter = (logsFilter: LogFilter) => {
    setLogsFilter(logsFilter);
  };

  const onSetSelection = (selection: StepSelection) => {
    setSelection(selection);
    setLogsFilter((previous) => ({
      ...previous,
      logQuery: selection.query !== '*' ? [{token: 'query', value: selection.query}] : [],
    }));
  };

  const executionPlan = run?.executionPlan;
  const {logQuery} = logsFilter;
  const selectedKeysForFilter = React.useMemo(() => {
    if (executionPlan) {
      return logQuery
        .filter((v) => v.token && v.token === 'query')
        .reduce((accum, v) => {
          return [...accum, ...queryStringToSelection(executionPlan, v.value)];
        }, []);
    }
    return [];
  }, [executionPlan, logQuery]);

  return (
    <RunContext.Provider value={run}>
      {run && <RunStatusToPageAttributes run={run} />}

      <LogsProvider
        key={runId}
        client={client}
        runId={runId}
        filter={logsFilter}
        selectedSteps={selectedKeysForFilter}
      >
        {({filteredNodes, hasTextFilter, textMatchNodes, loaded}) => (
          <RunWithData
            run={run}
            runId={runId}
            filteredNodes={filteredNodes}
            hasTextFilter={hasTextFilter}
            textMatchNodes={textMatchNodes}
            logsLoading={!loaded}
            logsFilter={logsFilter}
            selection={selection}
            onSetLogsFilter={onSetLogsFilter}
            onSetSelection={onSetSelection}
            onShowStateDetails={onShowStateDetails}
          />
        )}
      </LogsProvider>
    </RunContext.Provider>
  );
};

interface RunWithDataProps {
  run?: RunFragment;
  runId: string;
  selection: StepSelection;
  filteredNodes: (RunPipelineRunEventFragment & {clientsideKey: string})[];
  hasTextFilter: boolean;
  textMatchNodes: (RunPipelineRunEventFragment & {clientsideKey: string})[];
  logsFilter: LogFilter;
  logsLoading: boolean;
  onSetLogsFilter: (v: LogFilter) => void;
  onSetSelection: (v: StepSelection) => void;
  onShowStateDetails: (stepKey: string, logs: RunPipelineRunEventFragment[]) => void;
}

const RunWithData: React.FunctionComponent<RunWithDataProps> = ({
  run,
  runId,
  filteredNodes,
  hasTextFilter,
  textMatchNodes,
  logsFilter,
  logsLoading,
  selection,
  onSetLogsFilter,
  onSetSelection,
}) => {
  const [hideNonMatches, setHideNonMatches] = React.useState(true);
  const [launchPipelineReexecution] = useMutation<
    LaunchPipelineReexecution,
    LaunchPipelineReexecutionVariables
  >(LAUNCH_PIPELINE_REEXECUTION_MUTATION);
  const {activeRepo} = useWorkspaceState();
  const splitPanelContainer = React.createRef<SplitPanelContainer>();

  const onLaunch = async (style: ReExecutionStyle) => {
    if (!run || run.pipeline.__typename === 'UnknownPipeline' || !activeRepo) {
      return;
    }
    const variables = getReexecutionVariables({
      run,
      style,
      repositoryLocationName: activeRepo.address.location,
      repositoryName: activeRepo.address.name,
    });
    const result = await launchPipelineReexecution({variables});
    handleLaunchResult(run.pipeline.name, result, {openInNewWindow: false});
  };

  const onClickStep = (stepKey: string, evt: React.MouseEvent<any>) => {
    const index = selection.keys.indexOf(stepKey);
    let newSelected: string[];

    if (evt.shiftKey) {
      // shift-click to multi select steps
      newSelected = [...selection.keys];

      if (index !== -1) {
        // deselect the step if already selected
        newSelected.splice(index, 1);
      } else {
        // select the step otherwise
        newSelected.push(stepKey);
      }
    } else {
      if (selection.keys.length === 1 && index !== -1) {
        // deselect the step if already selected
        newSelected = [];
      } else {
        // select the step otherwise
        newSelected = [stepKey];
      }
    }

    onSetSelection({
      query: newSelected.join(', ') || '*',
      keys: newSelected,
    });
  };

  const onHideNonMatches = (checked: boolean) => setHideNonMatches(checked);

  return (
    <RunMetadataProvider logs={filteredNodes}>
      {(metadata) => (
        <SplitPanelContainer
          ref={splitPanelContainer}
          axis={'vertical'}
          identifier="run-gaant"
          firstInitialPercent={35}
          firstMinSize={40}
          first={
            logsLoading ? (
              <GaantChart.LoadingState runId={runId} />
            ) : run?.executionPlan ? (
              <GaantChart
                options={{
                  mode: GaantChartMode.WATERFALL_TIMED,
                }}
                toolbarLeftActions={
                  <FirstOrSecondPanelToggle axis={'vertical'} container={splitPanelContainer} />
                }
                toolbarActions={
                  <RunActionButtons
                    run={run}
                    executionPlan={run.executionPlan}
                    artifactsPersisted={run.executionPlan.artifactsPersisted}
                    onLaunch={onLaunch}
                    selection={selection}
                    selectionStates={selection.keys.map(
                      (key) => (key && metadata.steps[key]?.state) || IStepState.PREPARING,
                    )}
                  />
                }
                runId={runId}
                plan={run.executionPlan}
                metadata={metadata}
                selection={selection}
                onClickStep={onClickStep}
                onSetSelection={onSetSelection}
              />
            ) : (
              <NonIdealState icon={IconNames.ERROR} title="Unable to build execution plan" />
            )
          }
          second={
            <LogsContainer>
              <LogsToolbar
                filter={logsFilter}
                hideNonMatches={hideNonMatches}
                onHideNonMatches={onHideNonMatches}
                onSetFilter={onSetLogsFilter}
                selection={selection}
                steps={Object.keys(metadata.steps)}
                metadata={metadata}
              />
              <LogsScrollingTable
                filteredNodes={hasTextFilter && hideNonMatches ? textMatchNodes : filteredNodes}
                textMatchNodes={textMatchNodes}
                loading={logsLoading}
                filterKey={`${JSON.stringify(logsFilter)}-${JSON.stringify(hideNonMatches)}`}
                metadata={metadata}
              />
            </LogsContainer>
          }
        />
      )}
    </RunMetadataProvider>
  );
};

const LogsContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f1f6f9;
`;
