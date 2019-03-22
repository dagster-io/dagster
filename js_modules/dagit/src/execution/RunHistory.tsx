import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import {
  Popover,
  Button,
  Position,
  NonIdealState,
  Menu,
  MenuItem,
  Icon
} from "@blueprintjs/core";
import { RunHistoryRunFragment } from "./types/RunHistoryRunFragment";
import { titleForRun, RunStatus } from "./ExecutionUtils";

interface IRunHistoryProps {
  runs: RunHistoryRunFragment[];
  openRunIds: string[];
  onShowSessionFor: (run: RunHistoryRunFragment) => void;
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
    const { runs, openRunIds } = this.props;

    const history = (
      <HistoryPopoverBody>
        {runs.length === 0 ? (
          <div style={{ margin: 15 }}>
            <NonIdealState
              icon="history"
              title="Run History"
              description="No runs to display."
            />
          </div>
        ) : (
          <Menu>
            {[...runs].reverse().map(run => (
              <MenuItem
                key={run.runId}
                text={titleForRun(run)}
                labelElement={
                  openRunIds.indexOf(run.runId) !== -1 && (
                    <Icon icon="eye-open" />
                  )
                }
                icon={<RunStatus status={run.status} />}
                onClick={() => this.props.onShowSessionFor(run)}
              />
            ))}
          </Menu>
        )}
      </HistoryPopoverBody>
    );

    return (
      <Popover
        position={Position.BOTTOM_LEFT}
        content={history}
        target={
          <Button
            style={{ flexShrink: 0, whiteSpace: "nowrap" }}
            icon="history"
          />
        }
      />
    );
  }
}

const HistoryPopoverBody = styled.div`
  width: 200px;
  min-height: 150px;
  max-height: 400px;
  overflow: scroll;
`;
