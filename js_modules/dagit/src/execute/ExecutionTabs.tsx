import {Colors, Icon} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

import {
  IStorageData,
  applyChangesToSession,
  applyCreateSession,
  applyRemoveSession,
  applySelectSession,
} from '../LocalStorage';

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

class ExecutionTab extends React.Component<ExecutationTabProps, ExecutationTabState> {
  input = React.createRef<HTMLInputElement>();

  state = {editing: false};

  onDoubleClick = () => {
    if (!this.props.onChange) return;
    this.setState({editing: true}, () => {
      const el = this.input.current;
      if (el) {
        el.focus();
        el.select();
      }
    });
  };

  render() {
    const {title, onChange, onClick, onRemove, active, unsaved} = this.props;
    const {editing} = this.state;

    return (
      <TabContainer active={active || false} onDoubleClick={this.onDoubleClick} onClick={onClick}>
        {editing ? (
          <input
            ref={this.input}
            type="text"
            defaultValue={title}
            onKeyDown={(e) => e.keyCode === 13 && e.currentTarget.blur()}
            onChange={(e) => onChange && onChange(e.currentTarget.value)}
            onBlur={() => this.setState({editing: false})}
          />
        ) : unsaved ? (
          `${title}*`
        ) : (
          title
        )}
        {!editing && onRemove && (
          <RemoveButton
            onClick={(e) => {
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
  data: IStorageData;
  onSave: (data: IStorageData) => void;
}

function sessionNamesAndKeysHash(data: IStorageData) {
  return Object.values(data.sessions)
    .map((s) => s.name + s.key)
    .join(',');
}

export class ExecutionTabs extends React.Component<ExecutionTabsProps> {
  shouldComponentUpdate(prevProps: ExecutionTabsProps) {
    return (
      sessionNamesAndKeysHash(prevProps.data) !== sessionNamesAndKeysHash(this.props.data) ||
      prevProps.data.current !== this.props.data.current
    );
  }

  render() {
    const {data} = this.props;

    const onApply = (mutator: any, ...args: any[]) => {
      // note: this function /cannot/ use props bound to local vars above
      // because this component implements shouldComponentUpdate and data
      // used during render and captured here may be stale.
      this.props.onSave(mutator(this.props.data, ...args));
    };

    return (
      <ExecutionTabsContainer>
        {Object.keys(data.sessions).map((key) => (
          <ExecutionTab
            key={key}
            active={key === data.current}
            title={data.sessions[key].name}
            onClick={() => onApply(applySelectSession, key)}
            onChange={(name) => onApply(applyChangesToSession, key, {name})}
            onRemove={
              Object.keys(data.sessions).length > 1
                ? () => onApply(applyRemoveSession, key)
                : undefined
            }
          />
        ))}
        <ExecutionTab title="Add..." onClick={() => onApply(applyCreateSession)} />
      </ExecutionTabsContainer>
    );
  }
}

export const ExecutionTabsContainer = styled.div`
  padding-left: 10px;
  padding-top: 10px;
  display; flex;
  z-index: 1;
  flex-direction: row;
  border-bottom: 1px solid ${Colors.GRAY5};
`;

const TabContainer = styled.div<{active: boolean}>`
  position: relative;
  padding: 0 9px 2px 9px;
  display: inline-block;
  background: ${({active}) => (active ? Colors.WHITE : Colors.LIGHT_GRAY3)};
  color: ${({active}) => (active ? Colors.BLACK : Colors.DARK_GRAY3)};
  user-select: none;
  line-height: 28px;
  height: 30px;
  top: 1px;

  border: 1px solid ${Colors.GRAY5};
  border-bottom: 1px solid ${({active}) => (active ? 'transparent' : Colors.GRAY5)};
  border-right: 0;
  &:last-child {
    border-right: 1px solid ${Colors.GRAY5};
  }
  &:hover {
    background: ${({active}) => (active ? Colors.WHITE : Colors.LIGHT_GRAY5)};
  }
  input {
    line-height: 1.28581;
    font-size: 14px;
    border: 0;
    outline: none;
  }
  cursor: ${({active}) => (!active ? 'pointer' : 'inherit')};
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
