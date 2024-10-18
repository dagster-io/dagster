/* eslint-disable no-restricted-imports */
import {
  Menu as BlueprintMenu,
  MenuDivider as BlueprintMenuDivider,
  MenuItem as BlueprintMenuItem,
  Intent,
} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {Colors} from './Color';
import {Icon, IconName, IconWrapper} from './Icon';

interface Props extends React.ComponentProps<typeof BlueprintMenu> {}

export const Menu = (props: Props) => {
  return <StyledMenu {...props} />;
};

const intentToTextColor = (intent: React.ComponentProps<typeof BlueprintMenuItem>['intent']) => {
  switch (intent) {
    case 'primary':
      return Colors.accentBlue();
    case 'danger':
      return Colors.accentRed();
    case 'success':
      return Colors.accentGreen();
    case 'warning':
      return Colors.accentYellow();
    case 'none':
    default:
      return Colors.textDefault();
  }
};

const intentToIconColor = (intent: React.ComponentProps<typeof BlueprintMenuItem>['intent']) => {
  switch (intent) {
    case 'primary':
      return Colors.accentBlue();
    case 'danger':
      return Colors.accentRed();
    case 'success':
      return Colors.accentGreen();
    case 'warning':
      return Colors.accentYellow();
    case 'none':
    default:
      return Colors.textDefault();
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
    Omit<React.ComponentProps<typeof BlueprintMenuItem>, 'ref' | 'href' | 'icon'> {}

export const MenuItem = (props: ItemProps) => {
  const {icon, intent, ...rest} = props;
  return (
    <StyledMenuItem
      {...rest}
      $textColor={intentToTextColor(intent)}
      icon={iconWithColor(icon, intent)}
      tabIndex={0}
    />
  );
};

interface MenuExternalLinkProps
  extends CommonMenuItemProps,
    Omit<React.ComponentProps<typeof BlueprintMenuItem>, 'ref' | 'href' | 'icon'> {
  href: string;
}

/**
 * If you want to use a menu item as a link, use `MenuLink` and provide a `to` prop.
 */
export const MenuExternalLink = (props: MenuExternalLinkProps) => {
  const {icon, intent = 'none', ...rest} = props;
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
  border-top: 1px solid ${Colors.keylineDefault()};
  margin: 2px 0;

  :focus {
    outline: none;
  }

  && h6 {
    color: ${Colors.textLight()};
    padding: 8px 6px 2px;
    font-size: 12px;
    font-weight: 300;
    user-select: none;
  }
`;

const StyledMenu = styled(BlueprintMenu)`
  background-color: ${Colors.popoverBackground()};
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
  transition:
    background-color 50ms,
    box-shadow 150ms;
  align-items: flex-start;
  font-size: 14px;

  /**
   * Use margin instead of align-items: center because the contents of the menu item may wrap 
   * in unusual circumstances.
   */
  ${IconWrapper} {
    margin-top: 2px;
  }

  &.bp5-active,
  &.bp5-active:hover {
    background-color: ${Colors.backgroundBlue()};
    color: ${Colors.textDefault()};

    ${IconWrapper} {
      background-color: ${Colors.textDefault()};
    }
  }

  &.bp5-disabled ${IconWrapper} {
    opacity: 0.5;
  }

  &.bp5-active ${IconWrapper} {
    color: ${Colors.textDefault()};
  }

  ${IconWrapper}:first-child {
    margin-left: -4px;
  }

  &:hover {
    background: ${Colors.popoverBackgroundHover()};
    color: ${({$textColor}) => $textColor};
  }

  &:focus-visible {
    z-index: 1;
  }
`;
