/* eslint-disable no-restricted-imports */
import * as React from 'react';
import {
  Menu as BlueprintMenu,
  MenuDivider as BlueprintMenuDivider,
  MenuItem as BlueprintMenuItem,
  Intent,
} from '@blueprintjs/core';
import styled from 'styled-components';

import {
  colorAccentBlue,
  colorAccentGray,
  colorAccentGreen,
  colorAccentRed,
  colorAccentYellow,
  colorBackgroundBlue,
  colorKeylineDefault,
  colorPopoverBackground,
  colorPopoverBackgroundHover,
  colorTextDefault,
  colorTextLight,
} from '../theme/color';
import {Icon, IconName, IconWrapper} from './Icon';

interface Props extends React.ComponentProps<typeof BlueprintMenu> {}

export const Menu = (props: Props) => {
  return <StyledMenu {...props} />;
};

const intentToTextColor = (intent: React.ComponentProps<typeof BlueprintMenuItem>['intent']) => {
  switch (intent) {
    case 'primary':
      return colorAccentBlue();
    case 'danger':
      return colorAccentRed();
    case 'success':
      return colorAccentGreen();
    case 'warning':
      return colorAccentYellow();
    case 'none':
    default:
      return colorTextDefault();
  }
};

const intentToIconColor = (intent: React.ComponentProps<typeof BlueprintMenuItem>['intent']) => {
  switch (intent) {
    case 'primary':
      return colorAccentBlue();
    case 'danger':
      return colorAccentRed();
    case 'success':
      return colorAccentGreen();
    case 'warning':
      return colorAccentYellow();
    case 'none':
    default:
      return colorAccentGray();
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
    Omit<React.ComponentProps<typeof BlueprintMenuItem>, 'href' | 'icon'> {
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
  border-top: 1px solid ${colorKeylineDefault()};
  margin: 2px 0;

  :focus {
    outline: none;
  }

  && h6 {
    color: ${colorTextLight()};
    padding: 8px 6px 2px;
    font-size: 12px;
    font-weight: 300;
    user-select: none;
  }
`;

const StyledMenu = styled(BlueprintMenu)`
  background-color: ${colorPopoverBackground()};
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

  &.bp4-active,
  &.bp4-active:hover {
    background-color: ${colorBackgroundBlue()};
    color: ${colorTextDefault()};

    ${IconWrapper} {
      background-color: ${colorTextDefault()};
    }
  }

  &.bp4-disabled ${IconWrapper} {
    opacity: 0.5;
  }

  &.bp4-active ${IconWrapper} {
    color: ${colorTextDefault()};
  }

  ${IconWrapper}:first-child {
    margin-left: -4px;
  }

  &:hover {
    background: ${colorPopoverBackgroundHover()};
    color: ${({$textColor}) => $textColor};
  }

  &:focus-visible {
    z-index: 1;
  }
`;
