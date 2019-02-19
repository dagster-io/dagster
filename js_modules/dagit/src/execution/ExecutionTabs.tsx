import * as React from "react";
import styled from "styled-components";
import { Icon, Colors } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { RunStatus } from "./ExecutionUtils";

interface IExecutationTabProps {
  title: string;
  active?: boolean;
  unsaved?: boolean;
  run?: { status: "SUCCESS" | "NOT_STARTED" | "FAILURE" | "STARTED" };
  onChange?: (title: string) => void;
  onRemove?: () => void;
  onClick: () => void;
}

interface IExecutationTabState {
  editing: boolean;
}

export class ExecutionTab extends React.Component<
  IExecutationTabProps,
  IExecutationTabState
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
    const { title, onChange, onClick, onRemove, active, run, unsaved } = this.props;
    const { editing } = this.state;

    const Container = run ? RunTabContainer : TabContainer;

    return (
      <Container
        active={active || false}
        onDoubleClick={this.onDoubleClick}
        onClick={onClick}
      >
        {run && (
          <div style={{ marginRight: 4 }}>
            <RunStatus status={run.status} />
          </div>
        )}
        {editing ? (
          <input
            ref={this.input}
            type="text"
            defaultValue={title}
            onKeyDown={e => e.keyCode === 13 && e.currentTarget.blur()}
            onChange={e => onChange && onChange(e.currentTarget.value)}
            onBlur={() => this.setState({ editing: false })}
          />
        ) : (
          unsaved ? `${title}*` : title
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
      </Container>
    );
  }
}

export const ExecutionTabs = styled.div`
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

const RunTabContainer = styled(TabContainer)`
  font-family: monospace;
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
