import {Box, Colors, Icon, IconWrapper} from '@dagster-io/ui-components';
import * as React from 'react';
import {NavLink} from 'react-router-dom';
import {AppTopNavRightOfLogo} from 'shared/app/AppTopNav/AppTopNavRightOfLogo.oss';
import styled from 'styled-components';

import {GhostDaggyWithTooltip} from './GhostDaggy';
import {
  reloadFnForWorkspace,
  useRepositoryLocationReload,
} from '../../nav/useRepositoryLocationReload';
import {SearchDialog} from '../../search/SearchDialog';
import {LayoutContext} from '../LayoutProvider';
import {ShortcutHandler} from '../ShortcutHandler';

interface Props {
  children?: React.ReactNode;
  showStatusWarningIcon?: boolean;
  allowGlobalReload?: boolean;
}

export const AppTopNav = ({children, allowGlobalReload = false}: Props) => {
  const {reloading, tryReload} = useRepositoryLocationReload({
    scope: 'workspace',
    reloadFn: reloadFnForWorkspace,
  });

  return (
    <AppTopNavContainer>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
        <AppTopNavLogo />
        <AppTopNavRightOfLogo />
      </Box>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 12}} margin={{right: 20}}>
        {allowGlobalReload ? (
          <ShortcutHandler
            onShortcut={() => {
              if (!reloading) {
                tryReload();
              }
            }}
            shortcutLabel={`⌥R - ${reloading ? 'Reloading' : 'Reload all code locations'}`}
            shortcutFilter={(e) => e.altKey && e.code === 'KeyR'}
          >
            <div style={{width: '0px', height: '30px'}} />
          </ShortcutHandler>
        ) : null}
        <SearchDialog />
        {children}
      </Box>
    </AppTopNavContainer>
  );
};

export const AppTopNavLogo = () => {
  const {nav} = React.useContext(LayoutContext);
  const navButton = React.useRef<null | HTMLButtonElement>(null);

  const onToggle = React.useCallback(() => {
    if (navButton.current) {
      navButton.current.focus();
    }
    if (nav.isOpen) {
      nav.close();
    } else {
      nav.open();
    }
  }, [nav]);

  const onKeyDown = React.useCallback(
    (e: React.KeyboardEvent<HTMLButtonElement>) => {
      if (e.key === 'Escape' && nav.isOpen) {
        nav.close();
      }
    },
    [nav],
  );

  return (
    <LogoContainer>
      {nav.canOpen ? (
        <ShortcutHandler
          onShortcut={() => onToggle()}
          shortcutLabel="."
          shortcutFilter={(e) => e.key === '.'}
        >
          <NavButton onClick={onToggle} onKeyDown={onKeyDown} ref={navButton}>
            <Icon name="menu" color={Colors.navTextSelected()} size={24} />
          </NavButton>
        </ShortcutHandler>
      ) : null}
      <Box flex={{display: 'inline-flex'}} margin={{left: 8}}>
        <GhostDaggyWithTooltip />
      </Box>
    </LogoContainer>
  );
};

export const TopNavLink = styled(NavLink)`
  color: ${Colors.navText()};
  font-weight: 600;
  transition: color 50ms linear;
  padding: 24px 0;
  text-decoration: none;

  :hover {
    color: ${Colors.navTextHover()};
    text-decoration: none;
  }

  :active,
  &.active {
    color: ${Colors.navTextSelected()};
    text-decoration: none;
  }

  :focus {
    outline: none !important;
    color: ${Colors.navTextSelected()};
  }
`;

export const AppTopNavContainer = styled.div`
  background: ${Colors.navBackground()};
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  height: 64px;
`;

const LogoContainer = styled.div`
  cursor: pointer;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  padding-left: 12px;

  svg {
    transition: filter 100ms;
  }

  &:hover {
    svg {
      filter: brightness(90%);
    }
  }
`;

const NavButton = styled.button`
  border-radius: 20px;
  cursor: pointer;
  margin-left: 4px;
  outline: none;
  padding: 6px;
  border: none;
  background: ${Colors.navBackground()};
  display: block;

  ${IconWrapper} {
    transition: background 100ms linear;
  }

  :hover ${IconWrapper} {
    background: ${Colors.navTextHover()};
  }

  :active ${IconWrapper} {
    background: ${Colors.navTextHover()};
  }

  :focus {
    background: ${Colors.navButton()};
  }
`;
