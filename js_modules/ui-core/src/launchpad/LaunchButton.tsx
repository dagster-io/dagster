import {
  Button,
  Colors,
  Icon,
  IconName,
  Menu,
  MenuItem,
  Popover,
  Spinner,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';

import styles from './css/LaunchButton.module.css';
import {useConfirmation} from '../app/CustomConfirmationProvider';
import {ShortcutHandler} from '../app/ShortcutHandler';

export interface LaunchButtonConfiguration {
  title: string;
  disabled: boolean;
  warning?: React.ReactNode;
  scope?: string;
  onClick: (e: React.MouseEvent | KeyboardEvent) => Promise<any>;
  icon?: IconName | JSX.Element | 'dagster-spinner';
  tooltip?: string | JSX.Element;
}

enum LaunchButtonStatus {
  Ready = 'ready',
  Starting = 'starting',
  Disabled = 'disabled',
}

function useLaunchButtonCommonState({runCount, disabled}: {runCount: number; disabled: boolean}) {
  const [starting, setStarting] = React.useState(false);

  const onConfigSelected = async (
    e: React.MouseEvent | KeyboardEvent,
    option: LaunchButtonConfiguration,
  ) => {
    setStarting(true);
    await option.onClick(e);
    setStarting(false);
  };

  let forced: Partial<LaunchButtonConfiguration> = {};
  let status = disabled ? LaunchButtonStatus.Disabled : LaunchButtonStatus.Ready;

  if (starting) {
    status = LaunchButtonStatus.Starting;
    forced = {
      title: runCount === 1 ? 'Submitting run\u2026' : `Submitting ${runCount} runs\u2026`,
      disabled: true,
      icon: 'dagster-spinner',
    };
  }

  return {
    forced,
    status,
    onConfigSelected,
  };
}

interface LaunchButtonProps {
  config: LaunchButtonConfiguration;
  runCount: number;
}

export const LaunchButton = ({config, runCount}: LaunchButtonProps) => {
  const {forced, status, onConfigSelected} = useLaunchButtonCommonState({
    runCount,
    disabled: config.disabled,
  });
  const onClick = (e: React.MouseEvent | KeyboardEvent) => {
    if (status === LaunchButtonStatus.Ready) {
      onConfigSelected(e, config);
    }
  };
  return (
    <ShortcutHandler
      onShortcut={onClick}
      shortcutLabel="\u2325L"
      shortcutFilter={(e) => e.code === 'KeyL' && e.altKey}
    >
      <ButtonWithConfiguration
        status={status}
        {...config}
        {...forced}
        onClick={onClick}
        disabled={status === 'disabled'}
      />
    </ShortcutHandler>
  );
};

interface LaunchButtonDropdownProps {
  title: string;
  primary: LaunchButtonConfiguration;
  options: LaunchButtonConfiguration[];
  disabled?: boolean;
  tooltip?: string | JSX.Element;
  icon?: IconName | undefined;
  runCount: number;
}

export const LaunchButtonDropdown = ({
  title,
  primary,
  options,
  disabled,
  icon,
  tooltip,
  runCount,
}: LaunchButtonDropdownProps) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const allOptionsDisabled = options.every((d) => d.disabled);
  const {forced, status, onConfigSelected} = useLaunchButtonCommonState({
    runCount,
    disabled: disabled || allOptionsDisabled,
  });
  const popoverDisabled = status === LaunchButtonStatus.Disabled;

  return (
    <ShortcutHandler
      onShortcut={(e) => onConfigSelected(e, primary)}
      shortcutLabel="\u2325L"
      shortcutFilter={(e) => e.code === 'KeyL' && e.altKey}
    >
      <ButtonWithConfiguration
        status={status}
        title={title}
        joined="right"
        icon={icon}
        tooltip={tooltip}
        onClick={(e) => onConfigSelected(e, primary)}
        disabled={!!disabled}
        {...forced}
      />
      <Popover
        isOpen={isOpen}
        onInteraction={(nextOpen) => setIsOpen(nextOpen)}
        disabled={popoverDisabled}
        position="bottom-right"
        content={
          <Menu>
            {options.map((option, idx) => (
              <Tooltip key={idx} position="left" content={option.tooltip || ''}>
                <MenuItem
                  className={styles.launchMenuItem}
                  text={option.title}
                  disabled={option.disabled}
                  onClick={(e) => onConfigSelected(e, option)}
                  icon={option.icon !== 'dagster-spinner' ? option.icon : undefined}
                />
              </Tooltip>
            ))}
          </Menu>
        }
      >
        <Button
          role="button"
          className={styles.dropdownArrow}
          style={{cursor: status !== 'ready' ? 'normal' : 'pointer'}}
          icon={<Icon name="arrow_drop_down" />}
          intent="primary"
          disabled={popoverDisabled}
        />
      </Popover>
    </ShortcutHandler>
  );
};

interface ButtonWithConfigurationProps {
  title: string;
  warning?: React.ReactNode;
  status: LaunchButtonStatus;
  style?: React.CSSProperties;
  icon?: IconName | JSX.Element | 'dagster-spinner';
  joined?: 'left' | 'right';
  tooltip?: string | JSX.Element;
  onClick?: (e: React.MouseEvent) => void;
  disabled?: boolean;
}

// Basic helper components

const ButtonWithConfiguration = ({
  tooltip,
  icon,
  title,
  warning,
  status,
  style,
  onClick,
  joined,
  disabled,
}: ButtonWithConfigurationProps) => {
  const confirm = useConfirmation();

  const onClickWithWarning = async (e: React.MouseEvent) => {
    if (!onClick || disabled) {
      return;
    }
    if (warning) {
      try {
        await confirm({title: 'Are you sure?', description: warning});
      } catch {
        return;
      }
    }
    onClick(e);
  };

  return (
    <Tooltip position="left" canShow={!!tooltip} content={tooltip || ''}>
      <Button
        role="button"
        intent="primary"
        style={{
          ...style,
          borderTopRightRadius: joined === 'right' ? 0 : undefined,
          borderBottomRightRadius: joined === 'right' ? 0 : undefined,
          borderTopLeftRadius: joined === 'left' ? 0 : undefined,
          borderBottomLeftRadius: joined === 'left' ? 0 : undefined,
          borderLeft: joined === 'left' ? `1px solid ${Colors.keylineDefault()}` : 'transparent',
          cursor: status !== 'ready' ? 'normal' : 'pointer',
          marginLeft: joined ? '0' : '6px',
          ...(joined === 'right' ? {paddingRight: '8px'} : {}),
        }}
        onClick={onClickWithWarning}
        disabled={disabled}
        icon={
          icon === 'dagster-spinner' ? (
            <Spinner purpose="body-text" fillColor={Colors.accentReversed()} />
          ) : typeof icon === 'string' ? (
            <Icon name={icon} size={16} style={{textAlign: 'center', marginRight: 5}} />
          ) : (
            icon
          )
        }
      >
        <div className={styles.maxwidthText}>{title}</div>
      </Button>
    </Tooltip>
  );
};
