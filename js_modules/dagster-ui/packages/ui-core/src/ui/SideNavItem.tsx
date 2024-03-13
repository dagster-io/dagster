import {Box, Colors, IconWrapper, Tooltip, UnstyledButton} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

interface SideNavItemInterface {
  key: string;
  icon: React.ReactNode;
  label: React.ReactNode;
  disabled?: boolean;
  rightElement?: React.ReactNode;
  tooltip?: string;
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
  const {type, icon, label, rightElement, tooltip = '', disabled = false} = item;
  const content = (
    <Box
      padding={{vertical: 4, left: 12, right: 8}}
      flex={{direction: 'row', gap: 8, alignItems: 'center', justifyContent: 'space-between'}}
    >
      <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}} className="iconAndLabel">
        {icon}
        {label}
      </Box>
      <div>{rightElement}</div>
    </Box>
  );

  if (type === 'link' && !disabled) {
    return (
      <Tooltip canShow={!!tooltip} content={tooltip} placement="right" display="block">
        <StyledSideNavLink to={item.path} $active={active}>
          {content}
        </StyledSideNavLink>
      </Tooltip>
    );
  }

  return (
    <Tooltip canShow={!!tooltip} content={tooltip} placement="right" display="block">
      <StyledSideNavButton disabled={disabled} onClick={item.onClick}>
        {content}
      </StyledSideNavButton>
    </Tooltip>
  );
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

  .iconAndLabel {
    ${IconWrapper} {
      background-color: ${({$active}) => ($active ? Colors.textBlue() : Colors.textDefault())};
    }
  }
`;

const StyledSideNavButton = styled(UnstyledButton)`
  background-color: transparent;
  border-radius: 8px;
  color: ${Colors.textDefault()};
  display: block;
  font-size: 14px;
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
