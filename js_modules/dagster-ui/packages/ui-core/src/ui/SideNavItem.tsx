import {Box, Colors, IconWrapper, UnstyledButton} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

interface SideNavItemInterface {
  key: string;
  icon: React.ReactNode;
  label: React.ReactNode;
  rightElement?: React.ReactNode;
  tooltip?: React.ReactNode;
  onClick?: () => void;
}

export interface SideNavItemLinkConfig extends SideNavItemInterface {
  type: 'link';
  path: string;
}

export interface SideNavItemButtonConfig extends SideNavItemInterface {
  type: 'button';
  onClick: () => void;
}

export type SideNavItemConfig = SideNavItemLinkConfig | SideNavItemButtonConfig;

interface Props {
  active?: boolean;
  item: SideNavItemConfig;
}

export const SideNavItem = (props: Props) => {
  const {active = false, item} = props;
  const {type, icon, label} = item;
  const content = (
    <Box
      padding={{vertical: 4, horizontal: 12}}
      flex={{direction: 'row', gap: 8, alignItems: 'center'}}
    >
      {icon}
      {label}
    </Box>
  );

  if (type === 'link') {
    return (
      <StyledSideNavLink to={item.path} $active={active}>
        {content}
      </StyledSideNavLink>
    );
  }

  return <StyledSideNavButton onClick={item.onClick}>{content}</StyledSideNavButton>;
};

const StyledSideNavLink = styled(Link)<{$active: boolean}>`
  background-color: ${({$active}) => ($active ? Colors.backgroundBlue() : 'transparent')};
  border-radius: 8px;
  color: ${({$active}) => ($active ? Colors.textBlue() : Colors.textDefault())};
  display: block;
  line-height: 20px;
  text-decoration: none;
  transition: 100ms background-color linear;
  user-select: none;

  :focus {
    outline: none;
    background-color: ${({$active}) =>
      $active ? Colors.backgroundBlue() : Colors.backgroundLight()};
  }

  :hover,
  :active {
    background-color: ${({$active}) =>
      $active ? Colors.backgroundBlue() : Colors.backgroundLightHover()};
    color: ${({$active}) => ($active ? Colors.textBlue() : Colors.textDefault())};
    text-decoration: none;
  }

  ${IconWrapper} {
    background-color: ${({$active}) => ($active ? Colors.textBlue() : Colors.textDefault())};
  }
`;

const StyledSideNavButton = styled(UnstyledButton)`
  background-color: transparent;
  border-radius: 8px;
  color: ${Colors.textDefault()};
  display: block;
  line-height: 20px;
  text-decoration: none;
  transition: 100ms background-color linear;
  user-select: none;
  width: 100%;

  :focus {
    outline: none;
    background-color: ${Colors.backgroundLight()};
  }

  :hover,
  :active {
    background-color: ${Colors.backgroundLightHover()};
    color: ${Colors.textDefault()};
    text-decoration: none;
  }

  ${IconWrapper} {
    background-color: ${Colors.textDefault()};
  }
`;
