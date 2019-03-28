import * as React from "react";
import { ExecutionTabs, ExecutionTab } from "./ExecutionTabs";
import ExecutionStartButton from "./ExecutionStartButton";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { IExecutionSessionChanges, IExecutionSession } from "../LocalStorage";
import { isEqual, pick } from "lodash";

interface ITabBarProps {
  currentSession: IExecutionSession;
  sessions: { [name: string]: IExecutionSession };
  onExecute: (event: React.MouseEvent<HTMLDivElement, MouseEvent>) => void;
  onCreateSession: (initial?: IExecutionSessionChanges) => void;
  onSelectSession: (session: string) => void;
  onRemoveSession: (session: string) => void;
  onSaveSession: (session: string, changes: IExecutionSessionChanges) => void;
}

export default class TabBar extends React.Component<ITabBarProps> {
  shouldComponentUpdate(nextProps: ITabBarProps) {
    // TabBar can't be a PureComponent because the on* function props need to be
    // defined inline in the parent. Avoid rendering on every keystroke here.
    const keys = ["executing", "currentSession", "sessions"];
    return !isEqual(pick(nextProps, keys), pick(this.props, keys));
  }

  render() {
    const {
      onExecute,
      sessions,
      currentSession,
      onSelectSession,
      onSaveSession,
      onRemoveSession,
      onCreateSession
    } = this.props;

    return (
      <TabBarContainer className="bp3-dark">
        <ExecutionTabs>
          {Object.keys(sessions).map(key => (
            <ExecutionTab
              key={key}
              active={key === currentSession.key}
              title={sessions[key].name}
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
        <ExecutionStartButton onClick={onExecute} />
      </TabBarContainer>
    );
  }
}

const TabBarContainer = styled.div`
  height: 50px;
  display: flex;
  flex-direction: row;
  align-items: center;
  border-bottom: 1px solid ${Colors.DARK_GRAY5};
  background: ${Colors.BLACK};
  padding: 8px;
  z-index: 3;
`;
