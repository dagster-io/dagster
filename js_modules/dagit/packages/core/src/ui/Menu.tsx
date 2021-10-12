import {Menu, MenuDivider, MenuItem} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';
import {IconName, IconWIP, IconWrapper} from './Icon';

interface Props extends React.ComponentProps<typeof Menu> {}

export const MenuWIP: React.FC<Props> = (props) => {
  return <StyledMenu {...props} />;
};

const intentToTextColor = (intent: React.ComponentProps<typeof MenuItem>['intent']) => {
  switch (intent) {
    case 'primary':
      return ColorsWIP.Blue500;
    case 'danger':
      return ColorsWIP.Red500;
    case 'success':
      return ColorsWIP.Green500;
    case 'warning':
      return ColorsWIP.Yellow500;
    case 'none':
    default:
      return ColorsWIP.Gray900;
  }
};

const intentToIconColor = (intent: React.ComponentProps<typeof MenuItem>['intent']) => {
  switch (intent) {
    case 'primary':
      return ColorsWIP.Blue500;
    case 'danger':
      return ColorsWIP.Red500;
    case 'success':
      return ColorsWIP.Green500;
    case 'warning':
      return ColorsWIP.Yellow500;
    case 'none':
    default:
      return ColorsWIP.Gray900;
  }
};

interface ItemProps extends Omit<React.ComponentProps<typeof MenuItem>, 'icon'> {
  icon?: IconName | JSX.Element;
}

export const MenuItemWIP: React.FC<ItemProps> = (props) => {
  const {icon, intent, ...rest} = props;

  const textColor = intentToTextColor(intent);
  const iconColor = intentToIconColor(intent);
  const iconWithColor = () => {
    if (icon) {
      if (typeof icon === 'string') {
        return <IconWIP name={icon} color={iconColor} />;
      }
      return icon;
    }
    return null;
  };

  return <StyledMenuItem {...rest} $textColor={textColor} icon={iconWithColor()} />;
};

export const MenuDividerWIP = styled(MenuDivider)`
  border-top: 1px solid ${ColorsWIP.Gray100};
  margin: 2px 0;
`;

const StyledMenu = styled(Menu)`
  border-radius: 4px;
  padding: 8px 4px;
`;

interface StyledMenuItemProps extends React.ComponentProps<typeof MenuItem> {
  $textColor: string;
}

const StyledMenuItem = styled(MenuItem)<StyledMenuItemProps>`
  border-radius: 4px;
  color: ${({$textColor}) => $textColor};
  line-height: 20px;
  padding: 6px 8px 6px 12px;
  transition: background-color 50ms, box-shadow 150ms;
  align-items: center;

  &.bp3-intent-primary.bp3-active {
    background-color: ${ColorsWIP.Blue500};
  }

  &.bp3-disabled ${IconWrapper} {
    opacity: 0.5;
  }

  &.bp3-active ${IconWrapper} {
    color: ${ColorsWIP.White};
  }

  ${IconWrapper}:first-child {
    margin-left: -4px;
  }

  &:hover {
    background: ${ColorsWIP.Gray100};
    color: ${({$textColor}) => $textColor};
  }

  &:focus {
    color: ${({$textColor}) => $textColor};
    box-shadow: rgba(58, 151, 212, 0.6) 0 0 0 2px;
    outline: none;
  }
`;
