import {
  Button,
  Icon,
  IconName,
  Menu,
  MenuItem,
  Popover,
  Position,
  Tooltip,
} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ShortcutHandler} from 'src/app/ShortcutHandler';
import {WebsocketStatusContext} from 'src/app/WebsocketStatus';
import {Box} from 'src/ui/Box';
import {Spinner} from 'src/ui/Spinner';

export interface LaunchButtonConfiguration {
  title: string;
  disabled: boolean;
  scope?: string;
  onClick: () => Promise<any>;
  icon?: IconName | JSX.Element | 'dagster-spinner';
  tooltip?: string | JSX.Element;
}

enum LaunchButtonStatus {
  Ready = 'ready',
  Starting = 'starting',
  Disabled = 'disabled',
}

function useLaunchButtonCommonState({runCount, disabled}: {runCount: number; disabled: boolean}) {
  const websocketStatus = React.useContext(WebsocketStatusContext);
  const [starting, setStarting] = React.useState(false);

  const onConfigSelected = async (option: LaunchButtonConfiguration) => {
    setStarting(true);
    await option.onClick();
    setStarting(false);
  };

  let forced: Partial<LaunchButtonConfiguration> = {};
  let status = disabled ? LaunchButtonStatus.Disabled : LaunchButtonStatus.Ready;

  if (websocketStatus !== WebSocket.OPEN) {
    status = LaunchButtonStatus.Disabled;
    forced = {
      tooltip: 'The Dagit server is offline',
      disabled: true,
      icon: 'offline',
    };
  }

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
  small?: boolean;
  config: LaunchButtonConfiguration;
  runCount: number;
}

export const LaunchButton = ({config, runCount, small}: LaunchButtonProps) => {
  const {forced, status, onConfigSelected} = useLaunchButtonCommonState({
    runCount,
    disabled: config.disabled,
  });
  const onClick = () => {
    status === LaunchButtonStatus.Ready && onConfigSelected(config);
  };
  return (
    <ShortcutHandler
      onShortcut={onClick}
      shortcutLabel={`⌥L`}
      shortcutFilter={(e) => e.keyCode === 76 && e.altKey}
    >
      <ButtonWithConfiguration
        status={status}
        small={small}
        {...config}
        {...forced}
        onClick={onClick}
      />
    </ShortcutHandler>
  );
};

interface LaunchButtonDropdownProps {
  title: string;
  small?: boolean;
  primary: LaunchButtonConfiguration;
  options: LaunchButtonConfiguration[];
  disabled?: boolean;
  tooltip?: string | JSX.Element;
  icon?: IconName | undefined;
  runCount: number;
}

export const LaunchButtonDropdown = ({
  title,
  small,
  primary,
  options,
  disabled,
  icon,
  tooltip,
  runCount,
}: LaunchButtonDropdownProps) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const {forced, status, onConfigSelected} = useLaunchButtonCommonState({
    runCount,
    disabled: disabled || options.every((d) => d.disabled),
  });

  return (
    <ShortcutHandler
      onShortcut={() => onConfigSelected(primary)}
      shortcutLabel={`⌥L`}
      shortcutFilter={(e) => e.keyCode === 76 && e.altKey}
    >
      <ButtonWithConfiguration
        status={status}
        small={small}
        title={title}
        joined="right"
        icon={icon}
        tooltip={tooltip}
        onClick={() => onConfigSelected(primary)}
        disabled={!!disabled}
        {...forced}
      />
      <Popover
        isOpen={isOpen}
        onInteraction={(nextOpen) => setIsOpen(nextOpen)}
        disabled={status === LaunchButtonStatus.Disabled}
        position="bottom-right"
        content={
          <Menu>
            {options.map((option, idx) => (
              <Tooltip
                key={idx}
                hoverOpenDelay={300}
                position={Position.LEFT}
                openOnTargetFocus={false}
                targetTagName="div"
                content={option.tooltip}
              >
                <LaunchMenuItem
                  text={option.title}
                  disabled={option.disabled}
                  onClick={() => onConfigSelected(option)}
                  icon={option.icon === 'dagster-spinner' ? 'blank' : option.icon}
                />
              </Tooltip>
            ))}
          </Menu>
        }
      >
        <ButtonContainer
          role="button"
          status={status}
          small={small}
          style={{minWidth: 'initial', padding: '0 15px'}}
          icon={'caret-down'}
          joined={'left'}
        />
      </Popover>
    </ShortcutHandler>
  );
};

interface ButtonWithConfigurationProps {
  title: string;
  status: LaunchButtonStatus;
  style?: React.CSSProperties;
  icon?: IconName | JSX.Element | 'dagster-spinner';
  joined?: 'left' | 'right';
  tooltip?: string | JSX.Element;
  small?: boolean;
  onClick?: () => void;
  disabled?: boolean;
}

// Basic helper components

const ButtonWithConfiguration: React.FunctionComponent<ButtonWithConfigurationProps> = ({
  tooltip,
  icon,
  title,
  small,
  status,
  style,
  onClick,
  joined,
  disabled,
}) => {
  const sizeStyles = small ? {height: 24, minWidth: 120, paddingLeft: 15, paddingRight: 15} : {};

  return (
    <Tooltip
      position={Position.LEFT}
      openOnTargetFocus={false}
      targetTagName="div"
      content={tooltip}
    >
      <ButtonContainer
        role="button"
        style={{...sizeStyles, ...style}}
        status={status}
        onClick={onClick}
        joined={joined}
        disabled={disabled}
      >
        {icon === 'dagster-spinner' ? (
          <Box padding={{right: 8}}>
            <Spinner purpose="body-text" />
          </Box>
        ) : (
          <Icon
            icon={icon}
            iconSize={small ? 12 : 17}
            style={{textAlign: 'center', marginRight: 5}}
          />
        )}
        <ButtonText>{title}</ButtonText>
      </ButtonContainer>
    </Tooltip>
  );
};

const ButtonContainer = styled(Button)<{
  status: LaunchButtonStatus;
  small?: boolean;
  joined?: 'right' | 'left';
}>`
  &&& {
    height: ${({small}) => (small ? '24' : '30')}px;
    flex-shrink: 0;
    background: ${({status}) =>
      ({
        disabled: 'linear-gradient(to bottom, rgb(145, 145, 145) 30%, rgb(130, 130, 130) 100%);',
        ready: 'linear-gradient(to bottom, rgb(36, 145, 235) 30%, rgb(27, 112, 187) 100%);',
        starting: 'linear-gradient(to bottom, rgb(21, 89, 150) 30%, rgb(21, 89, 150) 100%);',
      }[status])};
    border-top: 1px solid rgba(255, 255, 255, 0.25);
    border-bottom: 1px solid rgba(0, 0, 0, 0.25);
    border-radius: 3px;
    border-top-${({joined}) => joined}-radius: 0;
    border-bottom-${({joined}) => joined}-radius: 0;
    transition: background 200ms linear;
    justify-content: center;
    align-items: center;
    display: inline-flex;
    color: ${({status}) => (status === 'disabled' ? 'rgba(255,255,255,0.5)' : 'white')};
    cursor: ${({status}) => (status !== 'ready' ? 'normal' : 'pointer')};
    z-index: 2;
    min-width: 150px;
    margin-left: ${({joined}) => (joined ? '0' : '6px')};
    padding: 0 25px;
    min-height: 0;

    &:hover,
    &.bp3-active {
      background: ${({status}) =>
        ({
          disabled: 'linear-gradient(to bottom, rgb(145, 145, 145) 30%, rgb(130, 130, 130) 100%);',
          ready: 'linear-gradient(to bottom, rgb(27, 112, 187) 30%, rgb(21, 89, 150) 100%);',
          starting: 'linear-gradient(to bottom, rgb(21, 89, 150) 30%, rgb(21, 89, 150) 100%);',
        }[status])};
    }

    path.bp3-spinner-head {
      stroke: white;
    }

    .bp3-icon {
      color: ${({status}) => (status === 'disabled' ? 'rgba(255,255,255,0.5)' : 'white')};
    }
    .bp3-button-text {
      display: flex;
      align-items: center;
    }
  }
`;

const ButtonText = styled.span`
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 350px;
`;

const LaunchMenuItem = styled(MenuItem)`
  max-width: 200px;
`;
