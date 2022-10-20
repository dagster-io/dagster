import {Box, ButtonLink, Colors, Icon, IconWrapper} from '@dagster-io/ui';
import * as React from 'react';
import styled, {css} from 'styled-components/macro';

import {useConfirmation} from '../app/CustomConfirmationProvider';
import {
  applyChangesToSession,
  applyRemoveSession,
  applySelectSession,
  IStorageData,
} from '../app/ExecutionSessionStorage';

interface ExecutationTabProps {
  canRemove?: boolean;
  title: string;
  active?: boolean;
  onChange?: (title: string) => void;
  onRemove?: () => void;
  onClick: () => void;
}

const LaunchpadTab = (props: ExecutationTabProps) => {
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
    <TabContainer $active={active || false} onDoubleClick={onDoubleClick} onClick={onClick}>
      {editing ? (
        <input
          ref={input}
          type="text"
          onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
          onChange={handleChange}
          onBlur={handleBlur}
          value={value}
          placeholder="Type a tab name…"
        />
      ) : (
        title
      )}
      {canRemove && !editing && onRemove ? (
        <RemoveButton onClick={onClickRemove}>
          <Icon name="close" color={Colors.Olive500} />
        </RemoveButton>
      ) : null}
    </TabContainer>
  );
};

const REMOVE_ALL_THRESHOLD = 3;

interface LaunchpadTabsProps {
  data: IStorageData;
  onCreate: () => void;
  onSave: (data: IStorageData) => void;
}

export const LaunchpadTabs = (props: LaunchpadTabsProps) => {
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
        title: 'Remove tab?',
        description: `The configuration for ${
          keyToRemove ? `"${sessions[keyToRemove].name}"` : 'this tab'
        } will be discarded.`,
      });
      onApply(applyRemoveSession, keyToRemove);
    }
  };

  const onRemoveAll = async () => {
    await confirm({
      title: 'Remove all tabs?',
      description: 'All configuration tabs will be discarded.',
    });

    let updatedData = data;
    sessionKeys.forEach((keyToRemove) => {
      updatedData = applyRemoveSession(updatedData, keyToRemove);
    });

    onSave(updatedData);
  };

  return (
    <Box border={{side: 'bottom', width: 1, color: Colors.KeylineGray}} padding={{top: 12}}>
      <LaunchpadTabsContainer>
        {sessionKeys.map((key) => (
          <LaunchpadTab
            canRemove={sessionCount > 1}
            key={key}
            active={key === data.current}
            title={sessions[key].name || 'Unnamed'}
            onClick={() => onApply(applySelectSession, key)}
            onChange={(name) => onApply(applyChangesToSession, key, {name})}
            onRemove={() => onRemove(key)}
          />
        ))}
        <LaunchpadTab title="+ Add..." onClick={onCreate} />
        {sessionKeys.length > REMOVE_ALL_THRESHOLD ? (
          <ButtonLink color={Colors.Red500} onClick={onRemoveAll}>
            <Box
              flex={{direction: 'row', gap: 4, alignItems: 'center'}}
              style={{whiteSpace: 'nowrap'}}
            >
              <Icon name="delete" color={Colors.Red500} />
              <div>Remove all</div>
            </Box>
          </ButtonLink>
        ) : null}
      </LaunchpadTabsContainer>
    </Box>
  );
};

const LaunchpadTabsContainer = styled.div`
  display: flex;
  flex-direction: row;
  font-size: 13px;
  gap: 8px;
  z-index: 1;
  flex-direction: row;
  padding-left: 12px;
  overflow-x: auto;
`;

const TabContainer = styled.div<{$active: boolean}>`
  align-items: center;
  user-select: none;
  padding: 8px 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  white-space: nowrap;

  ${({$active}) =>
    $active
      ? css`
          font-weight: 600;
          background-color: ${Colors.Gray100};
          color: ${Colors.ForestGreen};
          box-shadow: ${Colors.ForestGreen} 0 -2px 0 inset;
        `
      : css`
          font-weight: normal;
          background-color: ${Colors.Gray50};
          color: ${Colors.Gray300};
          box-shadow: ${Colors.Olive200} 0 -1px 0 inset;

          &:hover {
            background-color: ${Colors.Gray100};
            box-shadow: ${Colors.Olive500} 0 -1px 0 inset;
            color: ${Colors.Olive500};
          }
        `}

  &:last-child {
    padding-right: 12px;
  }

  input {
    background-color: transparent;
    font-size: 13px;
    border: 0;
    outline: none;
    padding: 0;
  }

  cursor: ${({$active}) => (!$active ? 'pointer' : 'inherit')};
`;

const RemoveButton = styled.button`
  background-color: transparent;
  border: 0;
  cursor: pointer;
  padding: 0;

  ${IconWrapper} {
    transition: background-color 100ms;
  }

  &:hover ${IconWrapper} {
    background-color: ${Colors.Olive700};
  }
`;
