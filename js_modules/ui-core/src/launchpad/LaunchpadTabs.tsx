import {Box, ButtonLink, Colors, Icon} from '@dagster-io/ui-components';
import clsx from 'clsx';
import * as React from 'react';

import styles from './css/LaunchpadTabs.module.css';
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
      if (onRemove) {
        onRemove();
      }
    },
    [onRemove],
  );

  const handleBlur = React.useCallback(() => {
    setEditing(false);
    if (onChange) {
      onChange(value);
    }
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
    <div
      className={clsx(styles.tabContainer, active ? styles.tabActive : styles.tabInactive)}
      onDoubleClick={onDoubleClick}
      onClick={onClick}
    >
      {editing ? (
        <input
          ref={input}
          type="text"
          onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
          onChange={handleChange}
          onBlur={handleBlur}
          value={value}
          placeholder="Type a tab name\u2026"
        />
      ) : (
        title
      )}
      {canRemove && !editing && onRemove ? (
        <button className={styles.removeButton} onClick={onClickRemove}>
          <Icon name="close" color={Colors.accentPrimary()} />
        </button>
      ) : null}
    </div>
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

  const onApply = <A extends unknown[]>(
    mutator: (data: IStorageData, ...args: A) => IStorageData,
    ...args: A
  ) => {
    onSave(mutator(data, ...args));
  };

  const onRemove = async (keyToRemove: string) => {
    if (sessionCount > 1) {
      await confirm({
        title: 'Remove tab?',
        description: `The configuration for ${
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
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
      <div className={styles.launchpadTabsContainer}>
        {sessionKeys.map((key) => (
          <LaunchpadTab
            canRemove={sessionCount > 1}
            key={key}
            active={key === data.current}
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            title={sessions[key]!.name || 'Unnamed'}
            onClick={() => onApply(applySelectSession, key)}
            onChange={(name) => onApply(applyChangesToSession, key, {name})}
            onRemove={() => onRemove(key)}
          />
        ))}
        <LaunchpadTab title="+ Add..." onClick={onCreate} />
        {sessionKeys.length > REMOVE_ALL_THRESHOLD ? (
          <Box
            background={Colors.backgroundDefault()}
            padding={{top: 8, left: 8, right: 12}}
            border="bottom"
            style={{position: 'sticky', right: 0}}
          >
            <ButtonLink color={Colors.textRed()} onClick={onRemoveAll}>
              <Box
                flex={{direction: 'row', gap: 4, alignItems: 'center'}}
                style={{whiteSpace: 'nowrap'}}
              >
                <Icon name="delete" color={Colors.textRed()} />
                <div>Remove all</div>
              </Box>
            </ButtonLink>
          </Box>
        ) : null}
      </div>
    </Box>
  );
};
