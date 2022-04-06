/* eslint-disable no-restricted-imports */
import {
  Intent,
  Menu as BlueprintMenu,
  MenuDivider as BlueprintMenuDivider,
  MenuItem as BlueprintMenuItem,
} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Colors} from './Colors';
import {IconName, Icon, IconWrapper} from './Icon';

interface Props extends React.ComponentProps<typeof BlueprintMenu> {}

export const Menu: React.FC<Props> = (props) => {
  return <StyledMenu {...props} />;
};

const intentToTextColor = (intent: React.ComponentProps<typeof BlueprintMenuItem>['intent']) => {
  switch (intent) {
    case 'primary':
      return Colors.Blue500;
    case 'danger':
      return Colors.Red500;
    case 'success':
      return Colors.Green500;
    case 'warning':
      return Colors.Yellow500;
    case 'none':
    default:
      return Colors.Gray900;
  }
};

const intentToIconColor = (intent: React.ComponentProps<typeof BlueprintMenuItem>['intent']) => {
  switch (intent) {
    case 'primary':
      return Colors.Blue500;
    case 'danger':
      return Colors.Red500;
    case 'success':
      return Colors.Green500;
    case 'warning':
      return Colors.Yellow500;
    case 'none':
    default:
      return Colors.Gray900;
  }
};

export const iconWithColor = (icon?: IconName | JSX.Element, intent?: Intent) => {
  if (icon) {
    if (typeof icon === 'string') {
      return <Icon name={icon} color={intentToIconColor(intent)} />;
    }
    return icon;
  }
  return null;
};

export interface CommonMenuItemProps {
  icon?: IconName | JSX.Element;
}

interface ItemProps
  extends CommonMenuItemProps,
    Omit<React.ComponentProps<typeof BlueprintMenuItem>, 'href' | 'icon'> {}

export const MenuItem: React.FC<ItemProps> = (props) => {
  const {icon, intent, ...rest} = props;
  return (
    <StyledMenuItem
      {...rest}
      $textColor={intentToTextColor(intent)}
      icon={iconWithColor(icon, intent)}
    />
  );
};

interface MenuExternalLinkProps
  extends CommonMenuItemProps,
    Omit<React.ComponentProps<typeof BlueprintMenuItem>, 'href' | 'icon'> {
  href: string;
}

/**
 * If you want to use a menu item as a link, use `MenuLink` and provide a `to` prop.
 */
export const MenuExternalLink: React.FC<MenuExternalLinkProps> = (props) => {
  const {icon, intent, ...rest} = props;
  return (
    <StyledMenuItem
      {...rest}
      target="_blank"
      rel="noreferrer nofollow"
      $textColor={intentToTextColor(intent)}
      icon={iconWithColor(icon, intent)}
    />
  );
};

export const MenuDivider = styled(BlueprintMenuDivider)`
  border-top: 1px solid ${Colors.Gray100};
  margin: 2px 0;
`;

const StyledMenu = styled(BlueprintMenu)`
  border-radius: 4px;
  padding: 8px 4px;
`;

interface StyledMenuItemProps extends React.ComponentProps<typeof BlueprintMenuItem> {
  $textColor: string;
}

const StyledMenuItem = styled(BlueprintMenuItem)<StyledMenuItemProps>`
  border-radius: 4px;
  color: ${({$textColor}) => $textColor};
  line-height: 20px;
  padding: 6px 8px 6px 12px;
  transition: background-color 50ms, box-shadow 150ms;
  align-items: flex-start;

  /**
   * Use margin instead of align-items: center because the contents of the menu item may wrap 
   * in unusual circumstances.
   */
  ${IconWrapper} {
    margin-top: 2px;
  }

  &.bp3-intent-primary.bp3-active {
    background-color: ${Colors.Blue500};

    ${IconWrapper} {
      background-color: ${Colors.White};
    }
  }

  &.bp3-disabled ${IconWrapper} {
    opacity: 0.5;
  }

  &.bp3-active ${IconWrapper} {
    color: ${Colors.White};
  }

  ${IconWrapper}:first-child {
    margin-left: -4px;
  }

  &:hover {
    background: ${Colors.Gray100};
    color: ${({$textColor}) => $textColor};
  }

  &:focus {
    color: ${({$textColor}) => $textColor};
    box-shadow: rgba(58, 151, 212, 0.6) 0 0 0 2px;
    outline: none;
  }
`;
