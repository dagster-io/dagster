import * as React from "react";
import styled from "styled-components";
import { Icon, Colors } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";

interface IExecutationTabProps {
  active?: boolean;
  title: string;
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
    const { title, onChange, onClick, onRemove, active } = this.props;
    const { editing } = this.state;
    return (
      <ExecutionTabContainer
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
      </ExecutionTabContainer>
    );
  }
}

export const ExecutionTabs = styled.div`
  background: ${Colors.BLACK};
  display; flex;
  z-index: 1;
  flex-direction: row;
`;

const ExecutionTabContainer = styled.div<{ active: boolean }>`
  color: ${({ active }) => (active ? Colors.WHITE : Colors.GRAY3)};
  padding: 12px 15px;
  display: inline-block;
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
