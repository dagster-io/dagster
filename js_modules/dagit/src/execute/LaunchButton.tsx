import {
  Button,
  Icon,
  IconName,
  Intent,
  Menu,
  MenuItem,
  Popover,
  Position,
  Spinner,
  Tooltip,
} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ShortcutHandler} from 'src/ShortcutHandler';
import {WebsocketStatusContext} from 'src/WebsocketStatus';

export interface LaunchButtonConfiguration {
  title: string;
  disabled: boolean;
  onClick: () => void;
  icon?: IconName | JSX.Element | 'dagster-spinner';
  tooltip?: string | JSX.Element;
}

export enum LaunchButtonStatus {
  Ready = 'ready',
  Starting = 'starting',
  Disabled = 'disabled',
}

function useLaunchButtonCommonState({disabled}: {disabled: boolean}) {
  const websocketStatus = React.useContext(WebsocketStatusContext);
  const [starting, setStarting] = React.useState(false);

  const onConfigSelected = async (option: LaunchButtonConfiguration) => {
    setStarting(true);
    await option.onClick();
    setTimeout(() => {
      setStarting(false);
    }, 300);
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
      title: 'Launching…',
      tooltip: 'Pipeline execution is in progress…',
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
}

export const LaunchButton: React.FunctionComponent<LaunchButtonProps> = ({config, small}) => {
  const {forced, status, onConfigSelected} = useLaunchButtonCommonState({
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
  options: LaunchButtonConfiguration[];
  disabled?: boolean;
  tooltip?: string;
  icon?: IconName | undefined;
}

export const LaunchButtonDropdown: React.FunctionComponent<LaunchButtonDropdownProps> = ({
  title,
  small,
  options,
  disabled,
  tooltip,
  icon,
}) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const {forced, status, onConfigSelected} = useLaunchButtonCommonState({
    disabled: disabled || options.every((d) => d.disabled),
  });

  return (
    <ShortcutHandler
      onShortcut={() => setIsOpen(true)}
      shortcutLabel={`⌥L`}
      shortcutFilter={(e) => e.keyCode === 76 && e.altKey}
    >
      <Popover
        isOpen={isOpen}
        onInteraction={(nextOpen) => setIsOpen(nextOpen)}
        disabled={status === LaunchButtonStatus.Disabled}
        position={'bottom'}
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
        <ButtonWithConfiguration
          status={status}
          small={small}
          title={title}
          rightIcon={'caret-down'}
          {...{tooltip, icon, ...forced}}
        />
      </Popover>
    </ShortcutHandler>
  );
};

interface ButtonWithConfigurationProps {
  title: string;
  status: LaunchButtonStatus;
  icon?: IconName | JSX.Element | 'dagster-spinner';
  rightIcon?: IconName;
  tooltip?: string | JSX.Element;
  small?: boolean;
  onClick?: () => void;
}

// Basic helper components

const ButtonWithConfiguration: React.FunctionComponent<ButtonWithConfigurationProps> = ({
  tooltip,
  icon,
  title,
  small,
  status,
  onClick,
  rightIcon,
}) => (
  <Tooltip
    hoverOpenDelay={300}
    position={Position.LEFT}
    openOnTargetFocus={false}
    targetTagName="div"
    content={tooltip}
  >
    <ButtonContainer
      role="button"
      style={small ? {height: 24, minWidth: 120, paddingLeft: 15, paddingRight: 15} : {}}
      status={status}
      onClick={onClick}
      rightIcon={rightIcon}
    >
      {icon === 'dagster-spinner' ? (
        <span style={{paddingRight: 6}}>
          <Spinner intent={Intent.NONE} size={small ? 12 : 17} />
        </span>
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

const ButtonContainer = styled(Button)<{
  status: LaunchButtonStatus;
  small?: boolean;
}>`
  &&& {
    height: ${({small}) => (small ? '24' : '30')}px;
    border-radius: 3px;
    flex-shrink: 0;
    background: ${({status}) =>
      ({
        disabled: 'linear-gradient(to bottom, rgb(145, 145, 145) 30%, rgb(130, 130, 130) 100%);',
        ready: 'linear-gradient(to bottom, rgb(36, 145, 235) 30%, rgb(27, 112, 187) 100%);',
        starting: 'linear-gradient(to bottom, rgb(21, 89, 150) 30%, rgb(21, 89, 150) 100%);',
      }[status])};
    border-top: 1px solid rgba(255, 255, 255, 0.25);
    border-bottom: 1px solid rgba(0, 0, 0, 0.25);
    transition: background 200ms linear;
    justify-content: center;
    align-items: center;
    display: inline-flex;
    color: ${({status}) => (status === 'disabled' ? 'rgba(255,255,255,0.5)' : 'white')};
    cursor: ${({status}) => (status !== 'ready' ? 'normal' : 'pointer')};
    z-index: 2;
    min-width: 150px;
    margin-left: 6px;
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
  max-width: 300px;
`;

const LaunchMenuItem = styled(MenuItem)`
  max-width: 200px;
`;
