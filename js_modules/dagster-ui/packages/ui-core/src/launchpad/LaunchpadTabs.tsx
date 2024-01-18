import * as React from 'react';
import styled, {css} from 'styled-components';

import {
  Box,
  ButtonLink,
  Icon,
  IconWrapper,
  colorAccentGray,
  colorAccentPrimary,
  colorAccentPrimaryHover,
  colorBackgroundDefault,
  colorBackgroundLight,
  colorBackgroundLighter,
  colorTextLight,
  colorTextLighter,
  colorTextRed,
} from '@dagster-io/ui-components';

import {useConfirmation} from '../app/CustomConfirmationProvider';
import {
  IStorageData,
  applyChangesToSession,
  applyRemoveSession,
  applySelectSession,
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
    (e: React.MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation();
      onRemove && onRemove();
    },
    [onRemove],
  );

  const handleBlur = React.useCallback(() => {
    setEditing(false);
    onChange && onChange(value);
  }, [onChange, value]);

  const handleChange = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => setValue(e.target.value),
    [],
  );

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
          <Icon name="close" color={colorAccentPrimary()} />
        </RemoveButton>
      ) : null}
    </TabContainer>
  );
};

const REMOVE_ALL_THRESHOLD = 3;

interface LaunchpadTabsProps {
  data: IStorageData;
  onCreate: () => void;
  onSave: (data: React.SetStateAction<IStorageData>) => void;
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
          keyToRemove && sessions[keyToRemove] ? `"${sessions[keyToRemove]!.name}"` : 'this tab'
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

    onSave((data) => {
      let updatedData = data;
      sessionKeys.forEach((keyToRemove) => {
        updatedData = applyRemoveSession(updatedData, keyToRemove);
      });
      return updatedData;
    });
  };

  return (
    <Box border="bottom" padding={{top: 12}}>
      <LaunchpadTabsContainer>
        {sessionKeys.map((key) => (
          <LaunchpadTab
            canRemove={sessionCount > 1}
            key={key}
            active={key === data.current}
            title={sessions[key]!.name || 'Unnamed'}
            onClick={() => onApply(applySelectSession, key)}
            onChange={(name) => onApply(applyChangesToSession, key, {name})}
            onRemove={() => onRemove(key)}
          />
        ))}
        <LaunchpadTab title="+ Add..." onClick={onCreate} />
        {sessionKeys.length > REMOVE_ALL_THRESHOLD ? (
          <Box
            background={colorBackgroundDefault()}
            padding={{top: 8, left: 8, right: 12}}
            border="bottom"
            style={{position: 'sticky', right: 0}}
          >
            <ButtonLink color={colorTextRed()} onClick={onRemoveAll}>
              <Box
                flex={{direction: 'row', gap: 4, alignItems: 'center'}}
                style={{whiteSpace: 'nowrap'}}
              >
                <Icon name="delete" color={colorTextRed()} />
                <div>Remove all</div>
              </Box>
            </ButtonLink>
          </Box>
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

  ::-webkit-scrollbar {
    display: none; /* Safari and Chrome */
  }
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
          background-color: ${colorBackgroundLighter()};
          color: ${colorAccentPrimary()};
          box-shadow: ${colorAccentPrimary()} 0 -2px 0 inset;
        `
      : css`
          font-weight: normal;
          background-color: ${colorBackgroundLight()};
          color: ${colorTextLighter()};
          box-shadow: ${colorAccentGray()} 0 -1px 0 inset;

          &:hover {
            background-color: ${colorBackgroundLight()};
            box-shadow: ${colorAccentGray()} 0 -1px 0 inset;
            color: ${colorTextLight()};
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
    background-color: ${colorAccentPrimaryHover()};
  }
`;
