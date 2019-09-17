import * as React from "react";
import styled from "styled-components";
import { Icon, Colors } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { IExecutionSessionChanges, IExecutionSession } from "../LocalStorage";

interface ExecutationTabProps {
  title: string;
  active?: boolean;
  unsaved?: boolean;
  onChange?: (title: string) => void;
  onRemove?: () => void;
  onClick: () => void;
}

interface ExecutationTabState {
  editing: boolean;
}

class ExecutionTab extends React.Component<
  ExecutationTabProps,
  ExecutationTabState
> {
  input = React.createRef<HTMLInputElement>();

  state = { editing: false };

  onDoubleClick = () => {
    if (!this.props.onChange) return;
    this.setState({ editing: true }, () => {
      const el = this.input.current;
      if (el) {
        el.focus();
        el.select();
      }
    });
  };

  render() {
    const { title, onChange, onClick, onRemove, active, unsaved } = this.props;
    const { editing } = this.state;

    return (
      <TabContainer
        active={active || false}
        onDoubleClick={this.onDoubleClick}
        onClick={onClick}
      >
        {editing ? (
          <input
            ref={this.input}
            type="text"
            defaultValue={title}
            onKeyDown={e => e.keyCode === 13 && e.currentTarget.blur()}
            onChange={e => onChange && onChange(e.currentTarget.value)}
            onBlur={() => this.setState({ editing: false })}
          />
        ) : unsaved ? (
          `${title}*`
        ) : (
          title
        )}
        {!editing && onRemove && (
          <RemoveButton
            onClick={e => {
              e.stopPropagation();
              onRemove();
            }}
          >
            <Icon icon={IconNames.CROSS} />
          </RemoveButton>
        )}
      </TabContainer>
    );
  }
}

interface ExecutionTabsProps {
  currentSession: IExecutionSession;
  sessions: { [name: string]: IExecutionSession };
  onCreateSession: (initial?: IExecutionSessionChanges) => void;
  onSelectSession: (session: string) => void;
  onRemoveSession: (session: string) => void;
  onSaveSession: (session: string, changes: IExecutionSessionChanges) => void;
}

export class ExecutionTabs extends React.Component<ExecutionTabsProps> {
  shouldComponentUpdate(prevProps: ExecutionTabsProps) {
    const prevSessions = Object.values(prevProps.sessions)
      .map(s => s.name + s.key)
      .join(",");
    const nextSessions = Object.values(this.props.sessions)
      .map(s => s.name + s.key)
      .join(",");
    return (
      prevSessions !== nextSessions ||
      prevProps.currentSession.key !== this.props.currentSession.key
    );
  }

  render() {
    const {
      sessions,
      currentSession,
      onSelectSession,
      onSaveSession,
      onRemoveSession,
      onCreateSession
    } = this.props;

    return (
      <ExecutionTabsContainer>
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
      </ExecutionTabsContainer>
    );
  }
}

export const ExecutionTabsContainer = styled.div`
  display; flex;
  z-index: 1;
  flex-direction: row;
  position: relative;
  top: 6px;
  `;

const TabContainer = styled.div<{ active: boolean }>`
  color: ${({ active }) => (active ? Colors.WHITE : Colors.GRAY3)};
  padding: 6px 9px;
  height: 36px
  display: inline-flex;
  align-items: center;
  border-left: 1px solid ${Colors.DARK_GRAY2};
  user-select: none;
  background: ${({ active }) => (active ? "#263238" : Colors.BLACK)};
  &:hover {
    background: ${({ active }) => (!active ? Colors.DARK_GRAY4 : "#263238")};
  }
  input {
    line-height: 1.28581;
    font-size: 14px;
    border: 0;
    outline: none;
  }
  cursor: ${({ active }) => (!active ? "pointer" : "inherit")};
`;

const RemoveButton = styled.div`
  display: inline-block;
  vertical-align: middle;
  margin-left: 10px;
  opacity: 0.2;
  &:hover {
    opacity: 0.6;
  }
`;
