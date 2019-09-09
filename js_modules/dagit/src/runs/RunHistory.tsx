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
  ButtonGroup,
  Spinner
} from "@blueprintjs/core";
import styled from "styled-components";
import { Link } from "react-router-dom";

import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import { RunHistoryRunFragment } from "./types/RunHistoryRunFragment";
import { titleForRun, RunStatus, IRunStatus } from "./RunUtils";
import { showCustomAlert } from "../CustomAlertProvider";
import * as qs from "query-string";
import { formatElapsedTime, formatStepKey } from "../Util";

function unixToString(unix: number | null) {
  if (!unix) {
    return null;
  }
  return new Date(unix * 1000).toLocaleString();
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
}

interface IRunHistoryState {
  sort: RunSort;
  statuses: IRunStatus[];
}

export default class RunHistory extends React.Component<
  IRunHistoryProps,
  IRunHistoryState
> {
  static fragments = {
    RunHistoryRunFragment: gql`
      fragment RunHistoryRunFragment on PipelineRun {
        runId
        status
        stepKeysToExecute
        mode
        environmentConfigYaml
        pipeline {
          name
        }
        stats {
          stepsSucceeded
          stepsFailed
          startTime
          endTime
          expectationsFailed
          expectationsSucceeded
          materializations
        }
        executionPlan {
          steps {
            key
          }
        }
      }
    `
  };

  state = {
    sort: RunSort.START_TIME_DSC,
    statuses: AllRunStatuses
  };

  sortRuns = (runs: RunHistoryRunFragment[]) => {
    const sortType = this.state.sort;
    if (sortType === null) {
      return runs;
    }
    return runs.sort((a, b) => {
      switch (sortType) {
        case RunSort.START_TIME_ASC:
          return (a.stats.startTime || 0) - (b.stats.startTime || 0);
        case RunSort.START_TIME_DSC:
          return (b.stats.startTime || 0) - (a.stats.startTime || 0);
        case RunSort.END_TIME_ASC:
          return (a.stats.endTime || 0) - (b.stats.endTime || 0);
        case RunSort.END_TIME_DSC:
        default:
          return (b.stats.endTime || 0) - (a.stats.endTime || 0);
      }
    });
  };

  render() {
    const { runs } = this.props;

    const mostRecentRun = runs[runs.length - 1];
    const sortedRuns = this.sortRuns(runs.slice(0, runs.length - 1)).filter(r =>
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

const MostRecentRun: React.FunctionComponent<{
  run: RunHistoryRunFragment;
}> = ({ run }) => (
  <div>
    <Header style={{ marginTop: 0 }}>Most Recent Run</Header>
    <RunRow run={run} />
  </div>
);

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
              key={s}
              active={props.statuses.includes(s)}
              onClick={() =>
                props.onSetStatuses(
                  props.statuses.includes(s)
                    ? props.statuses.filter(a => a !== s)
                    : props.statuses.concat([s])
                )
              }
            >
              {s === "STARTED" ? (
                <Spinner size={11} value={0.4} />
              ) : (
                <RunStatus status={s} />
              )}
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
      <LegendColumn style={{ maxWidth: 40 }}></LegendColumn>
      <LegendColumn style={{ flex: 2.3 }}>Run</LegendColumn>
      <LegendColumn>Pipeline</LegendColumn>
      <LegendColumn>Execution Params</LegendColumn>
      <LegendColumn style={{ flex: 1.6 }}>Timing</LegendColumn>
    </Legend>
    {props.runs.map(run => (
      <RunRow run={run} key={run.runId} />
    ))}
  </div>
);

const RunRow: React.FunctionComponent<{ run: RunHistoryRunFragment }> = ({
  run
}) => {
  return (
    <RunRowContainer key={run.runId}>
      <RunRowColumn
        style={{ maxWidth: 30, paddingLeft: 0, textAlign: "center" }}
      >
        <RunStatus
          status={
            run.stats.startTime && run.stats.endTime ? run.status : "STARTED"
          }
        />
      </RunRowColumn>
      <RunRowColumn style={{ flex: 2.4 }}>
        <Link
          style={{ display: "block" }}
          to={`/p/${run.pipeline.name}/runs/${run.runId}`}
        >
          {titleForRun(run)}
        </Link>
        <RunDetails>
          {`${run.stats.stepsSucceeded}/${run.stats.stepsSucceeded +
            run.stats.stepsFailed} steps succeeded, `}
          <Link
            to={`/p/${run.pipeline.name}/runs/${run.runId}?q=type:materialization`}
          >{`${run.stats.materializations} materializations`}</Link>
          ,{" "}
          <Link
            to={`/p/${run.pipeline.name}/runs/${run.runId}?q=type:expectation`}
          >{`${run.stats.expectationsSucceeded}/${run.stats
            .expectationsSucceeded +
            run.stats.expectationsFailed} expectations passed`}</Link>
        </RunDetails>
      </RunRowColumn>
      <RunRowColumn>
        <Link
          style={{ display: "block" }}
          to={`/p/${run.pipeline.name}/explore/`}
        >
          <Icon icon="diagram-tree" /> {run.pipeline.name}
        </Link>
      </RunRowColumn>
      <RunRowColumn
        style={{
          display: "flex",
          alignItems: "flex-start"
        }}
      >
        <div style={{ flex: 1 }}>
          <div>{`Mode: ${run.mode}`}</div>

          {run.stepKeysToExecute && (
            <div>
              {run.stepKeysToExecute.length === 1
                ? `Step: ${run.stepKeysToExecute.join("")}`
                : `${run.stepKeysToExecute.length} Steps`}
            </div>
          )}
        </div>
        <Popover
          content={
            <Menu>
              <MenuItem
                text="View Configuration..."
                icon="share"
                onClick={() =>
                  showCustomAlert({
                    title: "Config",
                    body: (
                      <HighlightedCodeBlock
                        value={run.environmentConfigYaml}
                        languages={["yaml"]}
                      />
                    )
                  })
                }
              />
              <MenuItem
                text="Open in Execute View..."
                icon="edit"
                target="_blank"
                href={`/p/${run.pipeline.name}/execute/setup?${qs.stringify({
                  mode: run.mode,
                  config: run.environmentConfigYaml,
                  solidSubset: run.stepKeysToExecute
                    ? run.stepKeysToExecute.map(formatStepKey)
                    : undefined
                })}`}
              />
            </Menu>
          }
          position={"bottom"}
        >
          <Button minimal={true} icon="chevron-down" />
        </Popover>
      </RunRowColumn>
      <RunRowColumn style={{ flex: 1.6 }}>
        {run.stats.startTime ? (
          <div style={{ marginBottom: 4 }}>
            <Icon icon="calendar" /> {unixToString(run.stats.startTime)}
            <Icon
              icon="arrow-right"
              style={{ marginLeft: 10, marginRight: 10 }}
            />
            {unixToString(run.stats.endTime)}
          </div>
        ) : (
          <div style={{ marginBottom: 4 }}>
            <Icon icon="calendar" /> Starting...
          </div>
        )}
        <RunTime startUnix={run.stats.startTime} endUnix={run.stats.endTime} />
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
  padding-left: 10px;
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
  padding: 7px 10px;
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
const RunDetails = styled.div`
  font-size: 0.8rem;
  margin-top: 4px;
`;

class RunTime extends React.Component<{
  startUnix: number | null;
  endUnix: number | null;
}> {
  _interval?: NodeJS.Timer;
  _timeout?: NodeJS.Timer;

  componentDidMount() {
    if (this.props.endUnix) return;

    // align to the next second and then update every second so the elapsed
    // time "ticks" up. Our render method uses Date.now(), so all we need to
    // do is force another React render. We could clone the time into React
    // state but that is a bit messier.
    setTimeout(() => {
      this.forceUpdate();
      this._interval = setInterval(() => this.forceUpdate(), 1000);
    }, Date.now() % 1000);
  }

  componentWillUnmount() {
    if (this._timeout) clearInterval(this._timeout);
    if (this._interval) clearInterval(this._interval);
  }

  render() {
    const start = this.props.startUnix ? this.props.startUnix * 1000 : 0;
    const end = this.props.endUnix ? this.props.endUnix * 1000 : Date.now();

    return (
      <div>
        <Icon icon="time" /> {start ? formatElapsedTime(end - start) : ""}
      </div>
    );
  }
}
