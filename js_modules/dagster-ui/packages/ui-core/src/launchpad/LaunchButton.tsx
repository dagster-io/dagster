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
import styled from 'styled-components';

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
      title: runCount === 1 ? 'Submitting run…' : `Submitting ${runCount} runs…`,
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
      shortcutLabel="⌥L"
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
      shortcutLabel="⌥L"
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
              <Tooltip
                key={idx}
                hoverOpenDelay={300}
                position="left"
                openOnTargetFocus={false}
                targetTagName="div"
                content={option.tooltip || ''}
              >
                <LaunchMenuItem
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
        <ButtonContainer
          role="button"
          status={status}
          style={{minWidth: 'initial'}}
          icon={<Icon name="arrow_drop_down" />}
          intent="primary"
          joined="left"
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
    <Tooltip
      position="left"
      openOnTargetFocus={false}
      targetTagName="div"
      canShow={!!tooltip}
      content={tooltip || ''}
    >
      <ButtonContainer
        role="button"
        intent="primary"
        style={{...style}}
        status={status}
        onClick={onClickWithWarning}
        joined={joined}
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
        <MaxwidthText>{title}</MaxwidthText>
      </ButtonContainer>
    </Tooltip>
  );
};

const ButtonContainer = styled(Button)<{
  status: LaunchButtonStatus;
  joined?: 'right' | 'left';
}>`
  border-top-${({joined}) => joined}-radius: 0;
  border-bottom-${({joined}) => joined}-radius: 0;
  border-left: ${({joined}) =>
    joined === 'left' ? `1px solid ${Colors.keylineDefault()}` : 'transparent'};
  cursor: ${({status}) => (status !== 'ready' ? 'normal' : 'pointer')};
  margin-left: ${({joined}) => (joined ? '0' : '6px')};
  ${({joined}) => (joined === 'right' ? 'padding-right: 8px;' : null)}
`;

const MaxwidthText = styled.div`
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 350px;
`;

const LaunchMenuItem = styled(MenuItem)`
  max-width: 200px;
`;
