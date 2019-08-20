import * as React from "react";
import gql from "graphql-tag";
import {
  NonIdealState,
  Menu,
  MenuItem,
  Colors,
  Icon,
  Popover,
  Button,
  Position,
  ButtonGroup
} from "@blueprintjs/core";
import { RunHistoryRunFragment } from "./types/RunHistoryRunFragment";
import { titleForRun, RunStatus, IRunStatus } from "./RunUtils";
import styled from "styled-components";
import { Link } from "react-router-dom";

function dateString(timestamp: number) {
  if (timestamp === 0) {
    return null;
  }
  return new Date(timestamp).toLocaleString();
}

const EXAMPLE_ERROR = `sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL:  role "test" does not exist

(Background on this error at: http://sqlalche.me/e/e3q8)

  File "/Users/bengotow/Work/F376/Projects/dagster/python_modules/dagster/dagster/core/errors.py", line 104, in user_code_error_boundary
    yield
,  File "/Users/bengotow/Work/F376/Projects/dagster/python_modules/dagster/dagster/core/engine/engine_inprocess.py", line 568, in _user_event_sequence_for_step_compute_fn
    for event in gen:
,  File "/Users/bengotow/Work/F376/Projects/dagster/python_modules/dagster/dagster/core/execution/plan/compute.py", line 75, in _execute_core_compute
    for step_output in _yield_compute_results(compute_context, inputs, compute_fn):
,  File "/Users/bengotow/Work/F376/Projects/dagster/python_modules/dagster/dagster/core/execution/plan/compute.py", line 52, in _yield_compute_results
    for event in user_event_sequence:
,  File "/Users/bengotow/Work/F376/Projects/dagster/python_modules/dagster/dagster/core/definitions/decorators.py", line 336, in compute
    for item in result:
,  File "/Users/bengotow/Work/F376/Projects/dagster/examples/dagster_examples/airline_demo/solids.py", line 129, in _sql_solid
    context.resources.db_info.engine.execute(text(sql_statement))
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/engine/base.py", line 2165, in execute
    connection = self._contextual_connect(close_with_result=True)
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/engine/base.py", line 2226, in _contextual_connect
    self._wrap_pool_connect(self.pool.connect, None),
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/engine/base.py", line 2266, in _wrap_pool_connect
    e, dialect, self
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/engine/base.py", line 1536, in _handle_dbapi_exception_noconnection
    util.raise_from_cause(sqlalchemy_exception, exc_info)
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/util/compat.py", line 383, in raise_from_cause
    reraise(type(exception), exception, tb=exc_tb, cause=cause)
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/util/compat.py", line 128, in reraise
    raise value.with_traceback(tb)
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/engine/base.py", line 2262, in _wrap_pool_connect
    return fn()
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/pool/base.py", line 363, in connect
    return _ConnectionFairy._checkout(self)
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/pool/base.py", line 760, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/pool/base.py", line 492, in checkout
    rec = pool._do_get()
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/pool/impl.py", line 139, in _do_get
    self._dec_overflow()
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/util/langhelpers.py", line 68, in __exit__
    compat.reraise(exc_type, exc_value, exc_tb)
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/util/compat.py", line 129, in reraise
    raise value
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/pool/impl.py", line 136, in _do_get
    return self._create_connection()
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/pool/base.py", line 308, in _create_connection
    return _ConnectionRecord(self)
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/pool/base.py", line 437, in __init__
    self.__connect(first_connect_check=True)
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/pool/base.py", line 639, in __connect
    connection = pool._invoke_creator(self)
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/engine/strategies.py", line 114, in connect
    return dialect.connect(*cargs, **cparams)
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/sqlalchemy/engine/default.py", line 451, in connect
    return self.dbapi.connect(*cargs, **cparams)
,  File "/Users/bengotow/venvs/dagit/lib/python3.7/site-packages/psycopg2/__init__.py", line 130, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
`;

function elapsedTimeString(start: number, end?: number) {
  const s = ((end || Date.now()) - start) / 1000;
  return `${Math.ceil(s)} seconds`;
}

function getStartTime(run: RunHistoryRunFragment) {
  for (const log of run.logs.nodes) {
    if (log.__typename === "PipelineStartEvent") {
      return Number(log.timestamp);
    }
  }
  return 0;
}

function getEndTime(run: RunHistoryRunFragment) {
  for (const log of run.logs.nodes) {
    if (
      log.__typename === "PipelineSuccessEvent" ||
      log.__typename === "PipelineFailureEvent"
    ) {
      return Number(log.timestamp);
    }
  }
  return 0;
}

enum RunSort {
  START_TIME_ASC,
  START_TIME_DSC,
  END_TIME_ASC,
  END_TIME_DSC
}

const AllRunStatuses: IRunStatus[] = [
  "NOT_STARTED",
  "STARTED",
  "SUCCESS",
  "FAILURE"
];

function sortLabel(sort: RunSort) {
  switch (sort) {
    case RunSort.START_TIME_ASC:
      return "Start Time (Asc)";
    case RunSort.START_TIME_DSC:
      return "Start Time (Desc)";
    case RunSort.END_TIME_ASC:
      return "End Time (Asc)";
    case RunSort.END_TIME_DSC:
      return "End Time (Desc)";
  }
}

interface IRunHistoryProps {
  runs: RunHistoryRunFragment[];
  pipelineName: string;
}

export default class RunHistory extends React.Component<
  IRunHistoryProps,
  { sort: RunSort; statuses: IRunStatus[] }
> {
  static fragments = {
    RunHistoryRunFragment: gql`
      fragment RunHistoryRunFragment on PipelineRun {
        runId
        status
        pipeline {
          name
        }
        logs {
          nodes {
            __typename
            ... on MessageEvent {
              timestamp
            }
          }
        }
        executionPlan {
          steps {
            key
          }
        }
      }
    `
  };

  state = { sort: RunSort.START_TIME_DSC, statuses: AllRunStatuses };

  sortRuns = (runs: RunHistoryRunFragment[]) => {
    const sortType = this.state.sort;
    if (sortType === null) {
      return runs;
    }

    return runs.sort((a, b) => {
      switch (sortType) {
        case RunSort.START_TIME_ASC:
          return getStartTime(a) - getStartTime(b);
        case RunSort.START_TIME_DSC:
          return getStartTime(b) - getStartTime(a);
        case RunSort.END_TIME_ASC:
          return getEndTime(a) - getEndTime(b);
        case RunSort.END_TIME_DSC:
        default:
          return getEndTime(b) - getEndTime(a);
      }
    });
  };

  render() {
    const { runs } = this.props;

    const mostRecentRun = runs[0];
    const sortedRuns = this.sortRuns(runs.slice(1)).filter(r =>
      this.state.statuses.includes(r.status)
    );

    return (
      <RunsScrollContainer>
        {runs.length === 0 ? (
          <div style={{ marginTop: 100 }}>
            <NonIdealState
              icon="history"
              title="Pipeline Runs"
              description="No runs to display. Use the Execute tab to start a pipeline."
            />
          </div>
        ) : (
          <>
            <UpcomingRuns runs={[]} />
            <MostRecentRun run={mostRecentRun} />
            <RunTable
              runs={sortedRuns}
              sort={this.state.sort}
              statuses={this.state.statuses}
              onSetSort={sort => this.setState({ sort })}
              onSetStatuses={statuses => this.setState({ statuses })}
            />
          </>
        )}
      </RunsScrollContainer>
    );
  }
}

const UpcomingRuns: React.FunctionComponent<{ runs: [] }> = props => (
  <div>
    <Header style={{ marginTop: 0 }}>Upcoming Runs</Header>
    <div style={{ color: Colors.GRAY1 }}>
      There are no upcoming runs.{" "}
      <a href="#">
        Learn how to save config presets and schedule runs.{" "}
        <Icon icon="share" />
      </a>
    </div>
  </div>
);

const MostRecentRun: React.FunctionComponent<{
  run: RunHistoryRunFragment;
}> = props => (
  <div>
    <Header>Most Recent Run</Header>
    <RunRow run={Object.assign({}, props.run, { status: "FAILURE" })} />
    <RunError>{EXAMPLE_ERROR}</RunError>
  </div>
);

const RunError = styled.div`
  font-size: 11px;
  font-family: monospace;
  white-space: pre;
  color: ${Colors.RED3};
  max-height: 250px;
  overflow: scroll;
  padding: 10px 20px;
  background: ${Colors.LIGHT_GRAY3};
  margin-top: -10px;
  border: 1px solid ${Colors.LIGHT_GRAY1};
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
`;

interface RunTableProps {
  runs: RunHistoryRunFragment[];
  sort: RunSort;
  statuses: IRunStatus[];
  onSetStatuses: (statuses: IRunStatus[]) => void;
  onSetSort: (sort: RunSort) => void;
}

const RunTable: React.FunctionComponent<RunTableProps> = props => (
  <div>
    <Header>
      <div style={{ float: "right" }}>
        <ButtonGroup style={{ marginRight: 15 }}>
          {AllRunStatuses.map(s => (
            <Button
              active={props.statuses.includes(s)}
              onClick={() =>
                props.onSetStatuses(
                  props.statuses.includes(s)
                    ? props.statuses.filter(a => a !== s)
                    : props.statuses.concat([s])
                )
              }
            >
              <RunStatus status={s} />
            </Button>
          ))}
        </ButtonGroup>
        <Popover
          position={Position.BOTTOM_RIGHT}
          content={
            <Menu>
              {[
                RunSort.START_TIME_ASC,
                RunSort.START_TIME_DSC,
                RunSort.END_TIME_ASC,
                RunSort.END_TIME_DSC
              ].map((v, idx) => (
                <MenuItem
                  key={idx}
                  text={sortLabel(v)}
                  onClick={() => props.onSetSort(v)}
                />
              ))}
            </Menu>
          }
        >
          <Button
            icon={"sort"}
            rightIcon={"caret-down"}
            text={sortLabel(props.sort)}
          />
        </Popover>
      </div>
      {`Previous Runs (${props.runs.length})`}
    </Header>
    <Legend>
      <LegendColumn style={{ maxWidth: 110 }}>Status</LegendColumn>
      <LegendColumn>Run ID</LegendColumn>
      <LegendColumn>Pipeline</LegendColumn>
      <LegendColumn>Config</LegendColumn>
      <LegendColumn>Timing</LegendColumn>
    </Legend>
    {props.runs.map(run => (
      <RunRow run={run} />
    ))}
  </div>
);

const RunRow: React.FunctionComponent<{ run: RunHistoryRunFragment }> = ({
  run
}) => {
  const start = getStartTime(run);
  const end = getEndTime(run);
  return (
    <RunRowContainer key={run.runId}>
      <RunRowColumn style={{ maxWidth: 100 }}>
        <RunStatus status={run.status} />
      </RunRowColumn>
      <RunRowColumn>
        <Link
          style={{ display: "block" }}
          to={`/${run.pipeline.name}/runs/${run.runId}`}
        >
          {titleForRun(run)}
        </Link>
      </RunRowColumn>
      <RunRowColumn>
        <Link style={{ display: "block" }} to={`/${run.pipeline.name}/explore`}>
          <Icon icon="diagram-tree" /> {run.pipeline.name}
        </Link>
      </RunRowColumn>
      <RunRowColumn>
        {!isNaN(Number(run.runId[0])) ? "Preset: local_fast" : "Custom"}
      </RunRowColumn>
      <RunRowColumn>
        <div style={{ marginBottom: 4 }}>
          <Icon icon="calendar" /> {dateString(start)}
          <Icon
            icon="arrow-right"
            style={{ marginLeft: 10, marginRight: 10 }}
          />
          {dateString(end)}
        </div>
        <div>
          <Icon icon="time" /> {elapsedTimeString(start, end)}
        </div>
      </RunRowColumn>
    </RunRowContainer>
  );
};

const Header = styled.div`
  color: ${Colors.BLACK};
  font-size: 1.1rem;
  line-height: 3rem;
  margin-top: 40px;
`;
const Legend = styled.div`
  display: flex;
  margin-bottom: 9px;
`;
const LegendColumn = styled.div`
  flex: 1;
  color: #8a9ba8;
  text-transform: uppercase;
  font-size: 11px;
`;
const RunRowContainer = styled.div`
  display: flex;
  background: ${Colors.WHITE};
  color: ${Colors.DARK_GRAY5};
  border-bottom: 1px solid ${Colors.LIGHT_GRAY1};
  margin-bottom: 9px;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
  padding: 2px 10px;
  text-decoration: none;
`;
const RunRowColumn = styled.div`
  flex: 1;
  padding: 10px 5px;
  border-right: 1px solid ${Colors.LIGHT_GRAY3};
  &:last-child {
    border-right: none;
  }
`;
const RunsScrollContainer = styled.div`
  background-color: rgb(245, 248, 250);
  padding: 20px;
  overflow: scroll;
  min-height: calc(100vh - 50px);
`;
