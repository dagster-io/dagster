// eslint-disable-next-line no-restricted-imports
import {
  Box,
  Colors,
  CommonMenuItemProps,
  IconWrapper,
  iconWithColor,
  MenuItem,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link, LinkProps} from 'react-router-dom';
import styled from 'styled-components/macro';

interface MenuLinkProps
  extends CommonMenuItemProps,
    Omit<React.ComponentProps<typeof MenuItem>, 'icon' | 'onClick'>,
    LinkProps {}

/**
 * If you want to use a menu item as a link, use `MenuLink` and provide a `to` prop.
 */
export const MenuLink: React.FC<MenuLinkProps> = (props) => {
  const {icon, intent, text, disabled, ...rest} = props;

  if (disabled) {
    return <MenuItem disabled icon={icon} intent={intent} text={text} />;
  }
  return (
    <StyledMenuLink {...rest}>
      <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
        {iconWithColor(icon, intent)}
        <div>{text}</div>
      </Box>
    </StyledMenuLink>
  );
};

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
    color: ${Colors.Gray900};
    text-decoration: none;
  }

  &&&:hover {
    background: ${Colors.Gray100};
  }
`;
