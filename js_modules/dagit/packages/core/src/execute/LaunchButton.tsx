import * as React from 'react';
import styled from 'styled-components/macro';

import {ShortcutHandler} from '../app/ShortcutHandler';
import {ButtonWIP} from '../ui/Button';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP, IconName} from '../ui/Icon';
import {MenuWIP, MenuItemWIP} from '../ui/Menu';
import {Popover} from '../ui/Popover';
import {Spinner} from '../ui/Spinner';
import {Tooltip} from '../ui/Tooltip';
import {useTelemetryAction} from '../app/Telemetry'

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
  const [starting, setStarting] = React.useState(false);

  const onConfigSelected = async (option: LaunchButtonConfiguration) => {
    setStarting(true);
    await option.onClick();
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
  const [telemetryRequest] = useTelemetryAction("Clicked LaunchPad Button");
  const onClick = () => {
    telemetryRequest()
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
          <MenuWIP>
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
                  onClick={() => onConfigSelected(option)}
                  icon={option.icon !== 'dagster-spinner' ? option.icon : undefined}
                />
              </Tooltip>
            ))}
          </MenuWIP>
        }
      >
        <ButtonContainer
          role="button"
          status={status}
          style={{minWidth: 'initial'}}
          icon={<IconWIP name="arrow_drop_down" />}
          intent="primary"
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
  onClick?: () => void;
  disabled?: boolean;
}

// Basic helper components

const ButtonWithConfiguration: React.FunctionComponent<ButtonWithConfigurationProps> = ({
  tooltip,
  icon,
  title,
  status,
  style,
  onClick,
  joined,
  disabled,
}) => {
  return (
    <Tooltip position="left" openOnTargetFocus={false} targetTagName="div" content={tooltip || ''}>
      <ButtonContainer
        role="button"
        intent="primary"
        style={{...style}}
        status={status}
        onClick={onClick}
        joined={joined}
        disabled={disabled}
        icon={
          icon === 'dagster-spinner' ? (
            <Spinner purpose="body-text" fillColor={ColorsWIP.White} />
          ) : typeof icon === 'string' ? (
            <IconWIP name={icon} size={16} style={{textAlign: 'center', marginRight: 5}} />
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

const ButtonContainer = styled(ButtonWIP)<{
  status: LaunchButtonStatus;
  joined?: 'right' | 'left';
}>`
  border-top-${({joined}) => joined}-radius: 0;
  border-bottom-${({joined}) => joined}-radius: 0;
  border-left: ${({joined}) =>
    joined === 'left' ? `1px solid rgba(255,255,255,0.2)` : 'transparent'};
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

const LaunchMenuItem = styled(MenuItemWIP)`
  max-width: 200px;
`;
