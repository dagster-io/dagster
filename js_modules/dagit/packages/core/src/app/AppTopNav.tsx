import * as React from 'react';
import {Link, useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import navBarImage from '../images/nav-logo-icon.png';
import navTitleImage from '../images/nav-title.png';
import {InstanceWarningIcon} from '../nav/InstanceWarningIcon';
import {VersionNumber} from '../nav/VersionNumber';
import {WorkspaceWarningIcon} from '../nav/WorkspaceWarningIcon';
import {SearchDialog} from '../search/SearchDialog';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP, IconWrapper} from '../ui/Icon';

import {LayoutContext} from './LayoutProvider';
import {ShortcutHandler} from './ShortcutHandler';
import {WebSocketStatus} from './WebSocketProvider';

interface Props {
  searchPlaceholder: string;
}

export const AppTopNav: React.FC<Props> = ({children, searchPlaceholder}) => {
  const history = useHistory();
  const {nav} = React.useContext(LayoutContext);
  const navButton = React.useRef<null | HTMLButtonElement>(null);

  const onToggle = React.useCallback(() => {
    navButton.current && navButton.current.focus();
    nav.isOpen ? nav.close() : nav.open();
  }, [nav]);

  const onKeyDown = React.useCallback(
    (e) => {
      if (e.key === 'Escape' && nav.isOpen) {
        nav.close();
      }
    },
    [nav],
  );

  return (
    <AppTopNavContainer>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 24}}>
        <LogoContainer>
          <ShortcutHandler
            onShortcut={() => onToggle()}
            shortcutLabel="."
            shortcutFilter={(e) => e.key === '.'}
          >
            <NavButton onClick={onToggle} onKeyDown={onKeyDown} ref={navButton}>
              <IconWIP name="menu" color={ColorsWIP.White} size={24} />
            </NavButton>
          </ShortcutHandler>
          <Group direction="row" alignItems="center" spacing={12} margin={{left: 8}}>
            <div style={{position: 'relative', top: '1px'}}>
              <img
                alt="logo"
                src={navBarImage}
                style={{height: 30}}
                onClick={() => history.push('/')}
              />
              <LogoWebsocketStatus />
            </div>
            <div>
              <img src={navTitleImage} style={{height: 10}} alt="title" />
              <VersionNumber />
            </div>
          </Group>
        </LogoContainer>
        <SearchDialog searchPlaceholder={searchPlaceholder} />
      </Box>
      <Box flex={{direction: 'row', alignItems: 'center'}}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
          <ShortcutHandler
            onShortcut={() => history.push('/instance/runs')}
            shortcutLabel={`⌥1`}
            shortcutFilter={(e) => e.code === 'Digit1' && e.altKey}
          >
            <NavLink to="/instance/runs">Runs</NavLink>
          </ShortcutHandler>
          <ShortcutHandler
            onShortcut={() => history.push('/instance/assets')}
            shortcutLabel={`⌥2`}
            shortcutFilter={(e) => e.code === 'Digit2' && e.altKey}
          >
            <NavLink to="/instance/assets">Assets</NavLink>
          </ShortcutHandler>
          <ShortcutHandler
            onShortcut={() => history.push('/instance')}
            shortcutLabel={`⌥3`}
            shortcutFilter={(e) => e.code === 'Digit3' && e.altKey}
          >
            <NavLink to="/instance">
              <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
                Status
                <InstanceWarningIcon />
              </Box>
            </NavLink>
          </ShortcutHandler>
          <ShortcutHandler
            onShortcut={() => history.push('/workspace')}
            shortcutLabel={`⌥4`}
            shortcutFilter={(e) => e.code === 'Digit4' && e.altKey}
          >
            <NavLink to="/workspace">
              <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
                Workspace
                <WorkspaceWarningIcon />
              </Box>
            </NavLink>
          </ShortcutHandler>
        </Box>
        {children}
      </Box>
    </AppTopNavContainer>
  );
};

const NavLink = styled(Link)`
  color: ${ColorsWIP.Gray200};
  font-weight: 600;
  transition: color 50ms linear;
  padding: 24px 0;

  :hover,
  :active {
    color: ${ColorsWIP.White};
    text-decoration: none;
  }
`;

const AppTopNavContainer = styled.div`
  background: ${ColorsWIP.Gray900};
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
  padding: 0 0 0 4px;
  &:hover {
    img {
      filter: brightness(110%);
    }
  }
`;

const LogoWebsocketStatus = styled(WebSocketStatus)`
  position: absolute;
  top: 20px;
  left: 24px;
`;

const NavButton = styled.button`
  border-radius: 20px;
  cursor: pointer;
  margin-left: 4px;
  outline: none;
  padding: 6px;
  border: none;
  background: transparent;
  display: none;

  ${IconWrapper} {
    transition: background 100ms linear;
  }

  :hover ${IconWrapper} {
    background: ${ColorsWIP.Gray500};
  }

  :active ${IconWrapper} {
    background: ${ColorsWIP.Blue200};
  }

  :focus {
    background: ${ColorsWIP.Gray700};
  }

  @media (max-width: 1440px) {
    display: block;
  }
`;
