// eslint-disable-next-line no-restricted-imports
import {Intent, Menu, MenuDivider, MenuItem} from '@blueprintjs/core';
import * as React from 'react';
import {Link, LinkProps} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Box} from './Box';
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

const iconWithColor = (icon?: IconName | JSX.Element, intent?: Intent) => {
  if (icon) {
    if (typeof icon === 'string') {
      return <IconWIP name={icon} color={intentToIconColor(intent)} />;
    }
    return icon;
  }
  return null;
};

interface CommonMenuItemProps {
  icon?: IconName | JSX.Element;
}

interface ItemProps
  extends CommonMenuItemProps,
    Omit<React.ComponentProps<typeof MenuItem>, 'href' | 'icon'> {}

export const MenuItemWIP: React.FC<ItemProps> = (props) => {
  const {icon, intent, ...rest} = props;
  return (
    <StyledMenuItem
      {...rest}
      $textColor={intentToTextColor(intent)}
      icon={iconWithColor(icon, intent)}
    />
  );
};

interface MenuLinkProps
  extends CommonMenuItemProps,
    Omit<React.ComponentProps<typeof MenuItem>, 'icon' | 'onClick'>,
    LinkProps {}

/**
 * If you want to use a menu item as a link, use `MenuLink` and provide a `to` prop.
 */
export const MenuLink: React.FC<MenuLinkProps> = (props) => {
  const {icon, intent, text, ...rest} = props;

  return (
    <StyledMenuLink {...rest}>
      <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
        {iconWithColor(icon, intent)}
        <div>{text}</div>
      </Box>
    </StyledMenuLink>
  );
};

interface MenuExternalLinkProps
  extends CommonMenuItemProps,
    Omit<React.ComponentProps<typeof MenuItem>, 'href' | 'icon'> {
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
  align-items: flex-start;

  /**
   * Use margin instead of align-items: center because the contents of the menu item may wrap 
   * in unusual circumstances.
   */
  ${IconWrapper} {
    margin-top: 2px;
  }

  &.bp3-intent-primary.bp3-active {
    background-color: ${ColorsWIP.Blue500};

    ${IconWrapper} {
      background-color: ${ColorsWIP.White};
    }
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

const StyledMenuLink = styled(Link)`
  text-decoration: none;

  border-radius: 4px;
  display: block;
  line-height: 20px;
  padding: 6px 8px 6px 12px;
  transition: background-color 50ms, box-shadow 150ms;
  align-items: flex-start;
  user-select: none;

  /**
   * Use margin instead of align-items: center because the contents of the menu item may wrap 
   * in unusual circumstances.
   */
  ${IconWrapper} {
    margin-top: 2px;
  }

  ${IconWrapper}:first-child {
    margin-left: -4px;
  }

  &&&:link,
  &&&:visited,
  &&&:hover,
  &&&:active {
    color: ${ColorsWIP.Gray900};
    text-decoration: none;
  }

  &&&:hover {
    background: ${ColorsWIP.Gray100};
  }
`;
