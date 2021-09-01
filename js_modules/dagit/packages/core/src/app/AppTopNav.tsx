import {Colors, Icon} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import navBarImage from '../images/nav-logo-icon.png';
import navTitleImage from '../images/nav-title.png';
import {VersionNumber} from '../nav/VersionNumber';
import {SearchDialog} from '../search/SearchDialog';
import {Group} from '../ui/Group';

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
      <LogoContainer>
        <ShortcutHandler
          onShortcut={() => onToggle()}
          shortcutLabel="."
          shortcutFilter={(e) => e.key === '.'}
        >
          <NavButton onClick={onToggle} onKeyDown={onKeyDown} ref={navButton}>
            <Icon color={Colors.WHITE} icon={IconNames.MENU} iconSize={16} />
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
      <SearchDialog theme="dark" searchPlaceholder={searchPlaceholder} />
      {children}
    </AppTopNavContainer>
  );
};

const AppTopNavContainer = styled.div`
  background: ${Colors.DARK_GRAY2};
  display: flex;
  flex-direction: row;
  height: 48px;
`;

const LogoContainer = styled.div`
  cursor: pointer;
  display: flex;
  align-items: center;
  width: 280px;
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
  border-radius: 16px;
  cursor: pointer;
  margin-left: 4px;
  outline: none;
  padding: 6px;
  border: none;
  background: transparent;
  display: none;

  .bp3-icon svg {
    transition: fill 100ms linear;
  }

  :hover .bp3-icon svg {
    fill: ${Colors.GRAY5};
  }

  :active .bp3-icon svg {
    fill: ${Colors.BLUE5};
  }

  :focus {
    background: ${Colors.DARK_GRAY5};
  }

  @media (max-width: 1440px) {
    display: block;
  }
`;
