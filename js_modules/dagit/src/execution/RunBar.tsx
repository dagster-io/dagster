import * as React from "react";
import { ExecutionTabs, ExecutionTab } from "./ExecutionTabs";
import ExecutionStartButton from "./ExecutionStartButton";
import styled from "styled-components";
import gql from "graphql-tag";
import { Colors } from "@blueprintjs/core";
import { IExecutionSessionChanges, IExecutionSession } from "../LocalStorage";
import { RunBarRunFragment } from "./types/RunBarRunFragment";
import RunHistory from "./RunHistory";
import { titleForRun } from "./ExecutionUtils";
import { isEqual, pick } from "lodash";
import * as YAML from "yaml";

interface IRunBarProps {
  executing: boolean;
  currentSession: IExecutionSession;
  sessions: { [name: string]: IExecutionSession };
  runs: RunBarRunFragment[];
  onExecute: (event: React.MouseEvent<HTMLDivElement, MouseEvent>) => void;
  onCreateSession: (initial?: IExecutionSessionChanges) => void;
  onSelectSession: (session: string) => void;
  onRemoveSession: (session: string) => void;
  onSaveSession: (session: string, changes: IExecutionSessionChanges) => void;
}

export default class RunBar extends React.Component<IRunBarProps> {
  static fragments = {
    RunBarRunFragment: gql`
      fragment RunBarRunFragment on PipelineRun {
        runId
        status
        ...RunHistoryRunFragment
      }
      ${RunHistory.fragments.RunHistoryRunFragment}
    `
  };

  shouldComponentUpdate(nextProps: IRunBarProps) {
    // RunBar can't be a PureComponent because the on* function props need to be
    // defined inline in the parent. Avoid rendering on every keystroke here.
    const keys = ["executing", "currentSession", "sessions", "runs"];
    return !isEqual(pick(nextProps, keys), pick(this.props, keys));
  }

  render() {
    const {
      runs,
      executing,
      onExecute,
      sessions,
      currentSession,
      onSelectSession,
      onSaveSession,
      onRemoveSession,
      onCreateSession
    } = this.props;

    const openRunIds = Object.keys(sessions)
      .map(key => sessions[key].runId)
      .filter(s => !!s) as string[];

    return (
      <RunBarContainer className="bp3-dark">
        <ExecutionTabs>
          {Object.keys(sessions).map(key => (
            <ExecutionTab
              key={key}
              active={key === currentSession.key}
              title={sessions[key].name}
              unsaved={sessions[key].configChangedSinceRun}
              run={runs.find(r => r.runId === sessions[key].runId)}
              onClick={() => onSelectSession(key)}
              onChange={name => onSaveSession(key, { name })}
              onRemove={
                Object.keys(sessions).length > 1
                  ? () => onRemoveSession(key)
                  : undefined
              }
            />
          ))}
          <ExecutionTab
            title={"Add..."}
            onClick={() => {
              onCreateSession();
            }}
          />
        </ExecutionTabs>
        <div style={{ flex: 1 }} />
        <RunHistory
          runs={runs}
          openRunIds={openRunIds}
          onShowSessionFor={run => {
            const key = Object.keys(sessions).find(
              key => sessions[key].runId === run.runId
            );
            if (key) {
              onSelectSession(key);
            } else {
              onCreateSession({
                name: titleForRun(run),
                runId: run.runId,
                config: YAML.stringify(YAML.parse(run.config))
              });
            }
          }}
        />
        <ExecutionStartButton executing={executing} onClick={onExecute} />
      </RunBarContainer>
    );
  }
}

const RunBarContainer = styled.div`
  height: 50px;
  display: flex;
  flex-direction: row;
  align-items: center;
  border-bottom: 1px solid ${Colors.DARK_GRAY5};
  background: ${Colors.BLACK};
  padding: 8px;
  z-index: 3;
`;
