import * as React from "react";
import * as qs from "query-string";
import * as yaml from "yaml";
import { uniq } from "lodash";
import gql from "graphql-tag";
import {
  Button,
  ButtonGroup,
  Colors,
  Icon,
  Menu,
  MenuItem,
  NonIdealState,
  Popover,
  MenuDivider,
  Position,
  Spinner,
  Tooltip
} from "@blueprintjs/core";
import {
  Details,
  Header,
  Legend,
  LegendColumn,
  RowColumn,
  RowContainer,
  ScrollContainer
} from "../ListComponents";
import {
  IRunStatus,
  RunStatus,
  titleForRun,
  REEXECUTE_MUTATION,
  handleStartExecutionResult,
  unixTimestampToString
} from "./RunUtils";
import { formatElapsedTime } from "../Util";
import {
  TokenizingField,
  TokenizingFieldValue,
  SuggestionProvider,
  tokenizedValuesListFromString
} from "../TokenizingField";
import { HighlightedCodeBlock } from "../HighlightedCodeBlock";
import { Link } from "react-router-dom";
import { RunHistoryRunFragment } from "./types/RunHistoryRunFragment";
import { showCustomAlert } from "../CustomAlertProvider";
import styled from "styled-components";
import { useMutation } from "react-apollo";

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

function searchSuggestionsForRuns(
  runs: RunHistoryRunFragment[]
): SuggestionProvider[] {
  return [
    {
      token: "id",
      values: () => runs.map(r => r.runId)
    },
    {
      token: "pipeline",
      values: () => uniq(runs.map(r => r.pipeline.name))
    },
    {
      token: "mode",
      values: () => uniq(runs.map(r => r.mode))
    },
    {
      token: "stepKey",
      values: () =>
        uniq(
          runs.reduce<string[]>(
            (r, c) => r.concat(c.stepKeysToExecute || []),
            []
          )
        )
    }
  ];
}

function runMatchesSearch(
  { pipeline, mode, runId, stepKeysToExecute }: RunHistoryRunFragment,
  search: TokenizingFieldValue[]
) {
  if (search.length === 0) {
    return true;
  }
  return search.some(({ token, value }) => {
    if ((!token || token === "pipeline") && pipeline.name.includes(value)) {
      return true;
    }
    if ((!token || token === "mode") && mode.includes(value)) {
      return true;
    }
    if ((!token || token === "id") && runId.includes(value)) {
      return true;
    }
    if (
      (!token || token === "stepKey") &&
      stepKeysToExecute &&
      stepKeysToExecute.some(sk => sk.includes(value))
    ) {
      return true;
    }
    return false;
  });
}

interface RunHistoryProps {
  runs: RunHistoryRunFragment[];
  initialSearch: string;
}

interface RunHistoryState {
  sort: RunSort;
  search: TokenizingFieldValue[];
  statuses: IRunStatus[];
}

export default class RunHistory extends React.Component<
  RunHistoryProps,
  RunHistoryState
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
          ... on PipelineReference {
            name
          }
          ... on Pipeline {
            solids {
              name
            }
          }
        }
        stats {
          stepsSucceeded
          stepsFailed
          startTime
          endTime
          expectations
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

  constructor(props: RunHistoryProps) {
    super(props);

    const suggestions = searchSuggestionsForRuns([]);

    this.state = {
      sort: RunSort.START_TIME_DSC,
      search: props.initialSearch
        ? tokenizedValuesListFromString(props.initialSearch, suggestions)
        : [],
      statuses: AllRunStatuses
    };
  }

  sortRuns = (runs: RunHistoryRunFragment[]) => {
    const sortType = this.state.sort;
    if (sortType === null) {
      return runs;
    }
    return runs.sort((a, b) => {
      // To ensure that unstarted / unfinished runs are sorted correctly (above
      // recently finished runs in DESC order, etc.), we assign them a sort value
      // higher than all unix timestamps.
      const aStart = a.stats.startTime || Number.MAX_SAFE_INTEGER;
      const bStart = b.stats.startTime || Number.MAX_SAFE_INTEGER;
      const aEnd = a.stats.endTime || Number.MAX_SAFE_INTEGER;
      const bEnd = b.stats.endTime || Number.MAX_SAFE_INTEGER;
      switch (sortType) {
        case RunSort.START_TIME_ASC:
          return aStart - bStart;
        case RunSort.START_TIME_DSC:
          return bStart - aStart;
        case RunSort.END_TIME_ASC:
          return aEnd - bEnd;
        case RunSort.END_TIME_DSC:
        default:
          return bEnd - aEnd;
      }
    });
  };

  render() {
    const { runs } = this.props;
    const { statuses, search, sort } = this.state;

    const mostRecentRun = runs[runs.length - 1];
    const sortedRuns = this.sortRuns(runs.slice(0, runs.length - 1))
      .filter(r => statuses.includes(r.status))
      .filter(r => runMatchesSearch(r, search));

    return (
      <ScrollContainer>
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

            <div
              style={{
                display: "flex",
                alignItems: "baseline",
                justifyContent: "space-between"
              }}
            >
              <Header>{`Previous Runs (${sortedRuns.length})`}</Header>
              <Filters>
                <RunStatusToggles
                  value={statuses}
                  onChange={statuses => this.setState({ statuses })}
                />
                <div style={{ width: 15 }} />
                <TokenizingField
                  values={search}
                  onChange={search => this.setState({ search })}
                  suggestionProviders={searchSuggestionsForRuns(runs)}
                />
                <div style={{ width: 15 }} />
                <SortDropdown
                  value={sort}
                  onChange={sort => this.setState({ sort })}
                />
              </Filters>
            </div>

            <RunTable runs={sortedRuns} />
          </>
        )}
      </ScrollContainer>
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
}

const RunTable: React.FunctionComponent<RunTableProps> = props => (
  <div>
    <Legend>
      <LegendColumn style={{ maxWidth: 30 }}></LegendColumn>
      <LegendColumn style={{ flex: 2.4 }}>Run</LegendColumn>
      <LegendColumn>Pipeline</LegendColumn>
      <LegendColumn style={{ flex: 1 }}>Execution Params</LegendColumn>
      <LegendColumn style={{ flex: 1.8 }}>Timing</LegendColumn>
      <LegendColumn style={{ maxWidth: 50 }}></LegendColumn>
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
    <RowContainer key={run.runId} style={{ paddingRight: 3 }}>
      <RowColumn style={{ maxWidth: 30, paddingLeft: 0, textAlign: "center" }}>
        <RunStatus status={run.status} />
      </RowColumn>
      <RowColumn style={{ flex: 2.4 }}>
        <Link
          style={{ display: "block" }}
          to={`/p/${run.pipeline.name}/runs/${run.runId}`}
        >
          {titleForRun(run)}
        </Link>
        <Details>
          <Link
            to={`/p/${run.pipeline.name}/runs/${run.runId}?q=type:step_success`}
          >{`${run.stats.stepsSucceeded} steps succeeded, `}</Link>
          <Link
            to={`/p/${run.pipeline.name}/runs/${run.runId}?q=type:step_failure`}
          >
            {`${run.stats.stepsFailed} steps failed, `}{" "}
          </Link>
          <Link
            to={`/p/${run.pipeline.name}/runs/${run.runId}?q=type:materialization`}
          >{`${run.stats.materializations} materializations`}</Link>
          ,{" "}
          <Link
            to={`/p/${run.pipeline.name}/runs/${run.runId}?q=type:expectation`}
          >{`${run.stats.expectations} expectations passed`}</Link>
        </Details>
      </RowColumn>
      <RowColumn>
        {run.pipeline.__typename === "Pipeline" ? (
          <Link
            style={{ display: "block" }}
            to={`/p/${run.pipeline.name}/explore/`}
          >
            <Icon icon="diagram-tree" /> {run.pipeline.name}
          </Link>
        ) : (
          <>
            <Icon icon="diagram-tree" color={Colors.GRAY3} />
            &nbsp;
            <Tooltip content="This pipeline is not present in the currently loaded repository, so dagit can't browse the pipeline solids, but you can still view the logs.">
              {run.pipeline.name}
            </Tooltip>
          </>
        )}
      </RowColumn>
      <RowColumn>
        <div>
          <div>{`Mode: ${run.mode}`}</div>

          {run.stepKeysToExecute && (
            <div>
              {run.stepKeysToExecute.length === 1
                ? `Step: ${run.stepKeysToExecute.join("")}`
                : `${run.stepKeysToExecute.length} Steps`}
            </div>
          )}
        </div>
      </RowColumn>
      <RowColumn style={{ flex: 1.8, borderRight: 0 }}>
        {run.stats.startTime ? (
          <div style={{ marginBottom: 4 }}>
            <Icon icon="calendar" />{" "}
            {unixTimestampToString(run.stats.startTime)}
            <Icon
              icon="arrow-right"
              style={{ marginLeft: 10, marginRight: 10 }}
            />
            {unixTimestampToString(run.stats.endTime)}
          </div>
        ) : run.status === "FAILURE" ? (
          <div style={{ marginBottom: 4 }}> Failed to start</div>
        ) : (
          <div style={{ marginBottom: 4 }}>
            <Icon icon="calendar" /> Starting...
          </div>
        )}
        <RunTime startUnix={run.stats.startTime} endUnix={run.stats.endTime} />
      </RowColumn>
      <RowColumn style={{ maxWidth: 50 }}>
        <RunActionsMenu run={run} />
      </RowColumn>
    </RowContainer>
  );
};

const RunActionsMenu: React.FunctionComponent<{
  run: RunHistoryRunFragment;
}> = ({ run }) => {
  const [reexecute] = useMutation(REEXECUTE_MUTATION);

  return (
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
          <MenuDivider />
          <MenuItem
            text="Open in Execute Tab..."
            icon="edit"
            target="_blank"
            href={`/p/${run.pipeline.name}/execute/setup?${qs.stringify({
              mode: run.mode,
              config: run.environmentConfigYaml,
              solidSubset:
                run.pipeline.__typename === "Pipeline"
                  ? run.pipeline.solids.map(s => s.name)
                  : []
            })}`}
          />
          <MenuItem
            text="Re-execute"
            icon="repeat"
            onClick={async () => {
              const result = await reexecute({
                variables: {
                  executionParams: {
                    mode: run.mode,
                    environmentConfigData: yaml.parse(
                      run.environmentConfigYaml
                    ),
                    selector: {
                      name: run.pipeline.name,
                      solidSubset:
                        run.pipeline.__typename === "Pipeline"
                          ? run.pipeline.solids.map(s => s.name)
                          : []
                    }
                  }
                }
              });
              handleStartExecutionResult(run.pipeline.name, result, {
                openInNewWindow: false
              });
            }}
          />
        </Menu>
      }
      position={"bottom"}
    >
      <Button minimal={true} icon="more" />
    </Popover>
  );
};

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

const SortDropdown: React.FunctionComponent<{
  onChange: (v: RunSort) => void;
  value: RunSort;
}> = ({ value, onChange }) => (
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
          <MenuItem key={idx} text={sortLabel(v)} onClick={() => onChange(v)} />
        ))}
      </Menu>
    }
  >
    <Button icon={"sort"} rightIcon={"caret-down"} text={sortLabel(value)} />
  </Popover>
);

const RunStatusToggles: React.FunctionComponent<{
  value: IRunStatus[];
  onChange: (value: IRunStatus[]) => void;
}> = ({ value, onChange }) => (
  <ButtonGroup>
    {AllRunStatuses.map(s => (
      <Button
        key={s}
        active={value.includes(s)}
        onClick={() =>
          onChange(
            value.includes(s) ? value.filter(a => a !== s) : value.concat([s])
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
);

const Filters = styled.div`
  float: right;
  display: flex;
  align-items: center;
  margin-bottom: 14px;
`;
