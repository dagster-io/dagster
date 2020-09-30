import {NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import ApolloClient from 'apollo-client';
import gql from 'graphql-tag';
import * as React from 'react';
import {useMutation} from 'react-apollo';
import styled from 'styled-components/macro';

import {showCustomAlert} from 'src/CustomAlertProvider';
import {DagsterRepositoryContext} from 'src/DagsterRepositoryContext';
import PythonErrorInfo from 'src/PythonErrorInfo';
import {IStepState, RunMetadataProvider} from 'src/RunMetadataProvider';
import {FirstOrSecondPanelToggle, SplitPanelContainer} from 'src/SplitPanelContainer';
import {GaantChart, GaantChartMode} from 'src/gaant/GaantChart';
import {GetDefaultLogFilter, LogFilter, LogsProvider} from 'src/runs/LogsProvider';
import LogsScrollingTable from 'src/runs/LogsScrollingTable';
import LogsToolbar from 'src/runs/LogsToolbar';
import {RunActionButtons} from 'src/runs/RunActionButtons';
import {RunContext} from 'src/runs/RunContext';
import {RunStatusToPageAttributes} from 'src/runs/RunStatusToPageAttributes';
import {
  LAUNCH_PIPELINE_REEXECUTION_MUTATION,
  getReexecutionVariables,
  handleLaunchResult,
} from 'src/runs/RunUtils';
import {LaunchPipelineReexecutionVariables} from 'src/runs/types/LaunchPipelineReexecution';
import {RunFragment} from 'src/runs/types/RunFragment';
import {
  RunPipelineRunEventFragment,
  RunPipelineRunEventFragment_ExecutionStepFailureEvent,
} from 'src/runs/types/RunPipelineRunEventFragment';

interface RunProps {
  client: ApolloClient<any>;
  runId: string;
  run?: RunFragment;
}

interface RunState {
  logsFilter: LogFilter;
  query: string;
  selectedSteps: string[];
}

export class Run extends React.Component<RunProps, RunState> {
  static fragments = {
    RunFragment: gql`
      fragment RunFragment on PipelineRun {
        ...RunStatusPipelineRunFragment

        runConfigYaml
        runId
        canTerminate
        status
        mode
        tags {
          key
          value
        }
        rootRunId
        parentRunId
        pipeline {
          __typename
          ... on PipelineReference {
            name
            solidSelection
          }
        }
        pipelineSnapshotId
        executionPlan {
          steps {
            key
            inputs {
              dependsOn {
                key
                outputs {
                  name
                  type {
                    name
                  }
                }
              }
            }
          }
          artifactsPersisted
          ...GaantChartExecutionPlanFragment
        }
        stepKeysToExecute
      }

      ${RunStatusToPageAttributes.fragments.RunStatusPipelineRunFragment}
      ${GaantChart.fragments.GaantChartExecutionPlanFragment}
    `,
    RunPipelineRunEventFragment: gql`
      fragment RunPipelineRunEventFragment on PipelineRunEvent {
        ... on MessageEvent {
          message
          timestamp
          level
          stepKey
        }

        ...LogsScrollingTableMessageFragment
        ...RunMetadataProviderMessageFragment
      }

      ${RunMetadataProvider.fragments.RunMetadataProviderMessageFragment}
      ${LogsScrollingTable.fragments.LogsScrollingTableMessageFragment}
      ${PythonErrorInfo.fragments.PythonErrorFragment}
    `,
  };

  state: RunState = {
    logsFilter: GetDefaultLogFilter(),
    query: '*',
    selectedSteps: [],
  };

  onShowStateDetails = (stepKey: string, logs: RunPipelineRunEventFragment[]) => {
    const errorNode = logs.find(
      (node) => node.__typename === 'ExecutionStepFailureEvent' && node.stepKey === stepKey,
    ) as RunPipelineRunEventFragment_ExecutionStepFailureEvent;

    if (errorNode) {
      showCustomAlert({
        body: <PythonErrorInfo error={errorNode} />,
      });
    }
  };

  onSetLogsFilter = (logsFilter: LogFilter) => {
    this.setState({logsFilter});
  };

  onSetQuery = (query: string) => {
    this.setState({query});

    // filter the log following the DSL step selection
    this.setState((prevState) => {
      return {
        logsFilter: {
          ...prevState.logsFilter,
          values: query !== '*' ? [{token: 'query', value: query}] : [],
        },
      };
    });
  };

  onSetSelectedSteps = (selectedSteps: string[]) => {
    this.setState({selectedSteps});
  };

  render() {
    const {client, run, runId} = this.props;
    const {logsFilter, query, selectedSteps} = this.state;

    return (
      <RunContext.Provider value={run}>
        {run && <RunStatusToPageAttributes run={run} />}

        <LogsProvider
          key={runId}
          client={client}
          runId={runId}
          filter={logsFilter}
          selectedSteps={selectedSteps}
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
              query={query}
              selectedSteps={selectedSteps}
              onSetLogsFilter={this.onSetLogsFilter}
              onSetQuery={this.onSetQuery}
              onSetSelectedSteps={this.onSetSelectedSteps}
              onShowStateDetails={this.onShowStateDetails}
              getReexecutionVariables={getReexecutionVariables}
            />
          )}
        </LogsProvider>
      </RunContext.Provider>
    );
  }
}

interface RunWithDataProps {
  run?: RunFragment;
  runId: string;
  filteredNodes: (RunPipelineRunEventFragment & {clientsideKey: string})[];
  hasTextFilter: boolean;
  textMatchNodes: (RunPipelineRunEventFragment & {clientsideKey: string})[];
  logsFilter: LogFilter;
  query: string;
  selectedSteps: string[];
  logsLoading: boolean;
  onSetQuery: (v: string) => void;
  onSetSelectedSteps: (v: string[]) => void;
  onSetLogsFilter: (v: LogFilter) => void;
  onShowStateDetails: (stepKey: string, logs: RunPipelineRunEventFragment[]) => void;
  getReexecutionVariables: (input: {
    run: RunFragment;
    stepKeys?: string[];
    stepQuery?: string;
    resumeRetry?: boolean;
    repositoryLocationName: string;
    repositoryName: string;
  }) => LaunchPipelineReexecutionVariables | undefined;
}

const RunWithData: React.FunctionComponent<RunWithDataProps> = ({
  run,
  runId,
  filteredNodes,
  hasTextFilter,
  textMatchNodes,
  logsFilter,
  logsLoading,
  query,
  selectedSteps,
  onSetLogsFilter,
  onSetQuery,
  onSetSelectedSteps,
  getReexecutionVariables,
}) => {
  const [launchPipelineReexecution] = useMutation(LAUNCH_PIPELINE_REEXECUTION_MUTATION);
  const repoContext = React.useContext(DagsterRepositoryContext);
  const repository = repoContext?.repository;
  const repositoryLocation = repoContext?.repositoryLocation;

  const [hideNonMatches, setHideNonMatches] = React.useState(true);

  const splitPanelContainer = React.createRef<SplitPanelContainer>();
  const stepQuery = query !== '*' ? query : '';
  const onLaunch = async (stepKeys?: string[], resumeRetry?: boolean) => {
    if (!run || run.pipeline.__typename === 'UnknownPipeline') {
      return;
    }
    const variables = getReexecutionVariables({
      run,
      stepKeys,
      stepQuery,
      resumeRetry,
      repositoryLocationName: repositoryLocation?.name || '',
      repositoryName: repository?.name || '',
    });
    const result = await launchPipelineReexecution({variables});
    handleLaunchResult(run.pipeline.name, result, {openInNewWindow: false});
  };

  const onClickStep = (stepKey: string, evt: React.MouseEvent<any>) => {
    const index = selectedSteps.indexOf(stepKey);
    let newSelected: string[];

    if (evt.shiftKey) {
      // shift-click to multi select steps
      newSelected = [...selectedSteps];

      if (index !== -1) {
        // deselect the step if already selected
        newSelected.splice(index, 1);
      } else {
        // select the step otherwise
        newSelected.push(stepKey);
      }
    } else {
      if (selectedSteps.length === 1 && index !== -1) {
        // deselect the step if already selected
        newSelected = [];
      } else {
        // select the step otherwise
        newSelected = [stepKey];
      }
    }

    onSetSelectedSteps(newSelected);
    onSetQuery(newSelected.join(', ') || '*');
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
                    selectedSteps={selectedSteps}
                    selectedStepStates={selectedSteps.map(
                      (selectedStep) =>
                        (selectedStep && metadata.steps[selectedStep]?.state) ||
                        IStepState.PREPARING,
                    )}
                  />
                }
                runId={runId}
                plan={run.executionPlan}
                metadata={metadata}
                selectedSteps={selectedSteps}
                onClickStep={onClickStep}
                onSetSelectedSteps={onSetSelectedSteps}
                query={query}
                onSetQuery={onSetQuery}
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
