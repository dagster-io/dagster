import * as React from 'react';
import styled from 'styled-components/macro';

import {useConfirmation} from '../app/CustomConfirmationProvider';
import {
  applyChangesToSession,
  applyRemoveSession,
  applySelectSession,
  IStorageData,
} from '../app/LocalStorage';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';

interface ExecutationTabProps {
  canRemove?: boolean;
  title: string;
  active?: boolean;
  onChange?: (title: string) => void;
  onRemove?: () => void;
  onClick: () => void;
}

const ExecutionTab = (props: ExecutationTabProps) => {
  const {canRemove, title, onChange, onClick, onRemove, active} = props;

  const input = React.useRef<HTMLInputElement>(null);
  const [editing, setEditing] = React.useState(false);
  const [value, setValue] = React.useState(title);

  const onDoubleClick = React.useCallback(() => {
    if (onChange) {
      setEditing(true);
    }
  }, [onChange]);

  const onClickRemove = React.useCallback(
    (e) => {
      e.stopPropagation();
      onRemove && onRemove();
    },
    [onRemove],
  );

  const handleBlur = React.useCallback(() => {
    setEditing(false);
    onChange && onChange(value);
  }, [onChange, value]);

  const handleChange = React.useCallback((e) => setValue(e.target.value), []);

  React.useEffect(() => {
    const el = input.current;
    if (el && editing) {
      el.focus();
      el.select();
    }
  }, [editing]);

  return (
    <TabContainer active={active || false} onDoubleClick={onDoubleClick} onClick={onClick}>
      {editing ? (
        <input
          ref={input}
          type="text"
          onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
          onChange={handleChange}
          onBlur={handleBlur}
          value={value}
        />
      ) : (
        title
      )}
      {canRemove && !editing && onRemove ? (
        <RemoveButton onClick={onClickRemove}>
          <IconWIP name="close" />
        </RemoveButton>
      ) : null}
    </TabContainer>
  );
};

interface ExecutionTabsProps {
  data: IStorageData;
  onCreate: () => void;
  onSave: (data: IStorageData) => void;
}

export const ExecutionTabs = (props: ExecutionTabsProps) => {
  const {data, onCreate, onSave} = props;
  const {sessions} = data;
  const sessionKeys = Object.keys(sessions);
  const sessionCount = sessionKeys.length;

  const confirm = useConfirmation();

  const onApply = (mutator: any, ...args: any[]) => {
    onSave(mutator(data, ...args));
  };

  const onRemove = async (keyToRemove: string) => {
    if (sessionCount > 1) {
      await confirm({
        title: 'Discard tab?',
        description: `The configuration for ${
          keyToRemove ? `"${sessions[keyToRemove].name}"` : 'this tab'
        } will be discarded.`,
      });
      onApply(applyRemoveSession, keyToRemove);
    }
  };

  return (
    <ExecutionTabsContainer>
      {sessionKeys.map((key) => (
        <ExecutionTab
          canRemove={sessionCount > 1}
          key={key}
          active={key === data.current}
          title={sessions[key].name}
          onClick={() => onApply(applySelectSession, key)}
          onChange={(name) => onApply(applyChangesToSession, key, {name})}
          onRemove={() => onRemove(key)}
        />
      ))}
      <ExecutionTab title="Add..." onClick={onCreate} />
    </ExecutionTabsContainer>
  );
};

const ExecutionTabsContainer = styled.div`
  padding-left: 20px;
  padding-top: 12px;
  display; flex;
  z-index: 1;
  flex-direction: row;
  border-bottom: 1px solid ${ColorsWIP.Gray200};
`;

const TabContainer = styled.div<{active: boolean}>`
  position: relative;
  padding: 6px 8px;
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  background: ${({active}) => (active ? ColorsWIP.White : ColorsWIP.Gray100)};
  color: ${({active}) => (active ? ColorsWIP.Dark : ColorsWIP.Gray800)};
  user-select: none;
  top: 1px;

  border: 1px solid ${ColorsWIP.Gray200};
  border-bottom: 1px solid ${({active}) => (active ? 'transparent' : ColorsWIP.Gray200)};
  border-right: 0;
  &:last-child {
    border-right: 1px solid ${ColorsWIP.Gray200};
  }
  &:hover {
    background: ${({active}) => (active ? ColorsWIP.White : ColorsWIP.Gray50)};
  }
  input {
    line-height: 1.28581;
    font-size: 14px;
    border: 0;
    outline: none;
  }
  cursor: ${({active}) => (!active ? 'pointer' : 'inherit')};
`;

const RemoveButton = styled.button`
  border: 0;
  cursor: pointer;
  margin-left: 4px;
  opacity: 0.2;
  padding: 0;
  &:hover {
    opacity: 0.6;
  }
`;
