import * as React from "react";
import gql from "graphql-tag";
import { NonIdealState, Menu, MenuItem } from "@blueprintjs/core";
import {
  Table,
  Column,
  Cell,
  ColumnHeaderCell,
  SelectionModes
} from "@blueprintjs/table";
import { RunHistoryRunFragment } from "./types/RunHistoryRunFragment";
import { titleForRun, RunStatus } from "./RunUtils";

function dateString(timestamp: number) {
  if (timestamp === 0) {
    return null;
  }
  return new Date(timestamp).toLocaleString();
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

interface IRunHistoryProps {
  runs: RunHistoryRunFragment[];
  pipelineName: string;
}

export default class RunHistory extends React.Component<
  IRunHistoryProps,
  { sort: RunSort | null }
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

  constructor(props: IRunHistoryProps) {
    super(props);
    this.state = { sort: null };
  }

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
    const { runs, pipelineName } = this.props;

    const sortedRuns = this.sortRuns(runs);

    return (
      <div>
        {sortedRuns.length === 0 ? (
          <div style={{ marginTop: 100 }}>
            <NonIdealState
              icon="history"
              title="Pipeline Runs"
              description="No runs to display. Use the Execute tab to start a pipeline."
            />
          </div>
        ) : (
          <Table
            numRows={sortedRuns.length}
            columnWidths={[35, null, null, null, null]}
            selectionModes={SelectionModes.NONE}
          >
            <Column
              name=""
              cellRenderer={idx => (
                <Cell tooltip={sortedRuns[idx].status}>
                  {<RunStatus status={sortedRuns[idx].status} />}
                </Cell>
              )}
            />
            <Column
              name="Run ID"
              cellRenderer={idx => (
                <Cell tooltip={sortedRuns[idx].runId}>
                  <a href={`/${pipelineName}/runs/${sortedRuns[idx].runId}`}>
                    {titleForRun(sortedRuns[idx])}
                  </a>
                </Cell>
              )}
            />
            <Column
              name="Pipeline"
              cellRenderer={idx => <Cell>{sortedRuns[idx].pipeline.name}</Cell>}
            />
            <Column
              cellRenderer={idx => (
                <Cell>{dateString(getStartTime(sortedRuns[idx]))}</Cell>
              )}
              columnHeaderCellRenderer={() => (
                <ColumnHeaderCell
                  name={"Start Time"}
                  menuRenderer={() => (
                    <Menu>
                      <MenuItem
                        icon="sort-asc"
                        onClick={() => {
                          this.setState({ sort: RunSort.START_TIME_ASC });
                        }}
                        text="Sort Asc"
                      />
                      <MenuItem
                        icon="sort-desc"
                        onClick={() => {
                          this.setState({ sort: RunSort.START_TIME_DSC });
                        }}
                        text="Sort Desc"
                      />
                    </Menu>
                  )}
                />
              )}
            />
            <Column
              cellRenderer={idx => (
                <Cell>{dateString(getEndTime(sortedRuns[idx]))}</Cell>
              )}
              columnHeaderCellRenderer={() => (
                <ColumnHeaderCell
                  name={"End Time"}
                  menuRenderer={() => (
                    <Menu>
                      <MenuItem
                        icon="sort-asc"
                        onClick={() => {
                          this.setState({ sort: RunSort.END_TIME_ASC });
                        }}
                        text="Sort Asc"
                      />
                      <MenuItem
                        icon="sort-desc"
                        onClick={() => {
                          this.setState({ sort: RunSort.END_TIME_DSC });
                        }}
                        text="Sort Desc"
                      />
                    </Menu>
                  )}
                />
              )}
            />
          </Table>
        )}
      </div>
    );
  }
}
