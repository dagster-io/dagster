import * as React from "react";
import gql from "graphql-tag";
import { NonIdealState, Menu, MenuItem, Icon } from "@blueprintjs/core";
import { RunHistoryRunFragment } from "./types/RunHistoryRunFragment";
import { titleForRun, RunStatus } from "./RunUtils";

interface IRunHistoryProps {
  runs: RunHistoryRunFragment[];
  pipelineName: string;
}

export default class RunHistory extends React.Component<IRunHistoryProps> {
  static fragments = {
    RunHistoryRunFragment: gql`
      fragment RunHistoryRunFragment on PipelineRun {
        runId
        status
        config
        pipeline {
          name
        }
        executionPlan {
          steps {
            name
          }
        }
      }
    `
  };

  render() {
    const { runs, pipelineName } = this.props;

    return (
      <div>
        {runs.length === 0 ? (
          <div style={{ marginTop: 100 }}>
            <NonIdealState
              icon="history"
              title="Pipeline Runs"
              description="No runs to display. Use the Execute tab to start a pipeline."
            />
          </div>
        ) : (
          <Menu>
            {[...runs].reverse().map(run => (
              <MenuItem
                key={run.runId}
                href={`/${pipelineName}/runs/${run.runId}`}
                text={titleForRun(run)}
                // labelElement={
                //   openRunIds.indexOf(run.runId) !== -1 && (
                //     <Icon icon="eye-open" />
                //   )
                // }
                icon={<RunStatus status={run.status} />}
              />
            ))}
          </Menu>
        )}
      </div>
    );
  }
}
