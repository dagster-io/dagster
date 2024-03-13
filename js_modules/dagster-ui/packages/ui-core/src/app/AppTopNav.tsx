import {Box, Colors, Icon, IconWrapper, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link, NavLink, useHistory} from 'react-router-dom';
import styled from 'styled-components';

import {useFeatureFlags} from './Flags';
import {LayoutContext} from './LayoutProvider';
import {ShortcutHandler} from './ShortcutHandler';
import {WebSocketStatus} from './WebSocketProvider';
import {DeploymentStatusIcon} from '../nav/DeploymentStatusIcon';
import {VersionNumber} from '../nav/VersionNumber';
import {
  reloadFnForWorkspace,
  useRepositoryLocationReload,
} from '../nav/useRepositoryLocationReload';
import {SearchDialog} from '../search/SearchDialog';

type AppNavLinkType = {
  title: string;
  element: React.ReactNode;
};
interface Props {
  children?: React.ReactNode;
  searchPlaceholder: string;
  rightOfSearchBar?: React.ReactNode;
  showStatusWarningIcon?: boolean;
  getNavLinks?: (navItems: AppNavLinkType[]) => React.ReactNode;
  allowGlobalReload?: boolean;
}

export const AppTopNav = ({
  children,
  rightOfSearchBar,
  searchPlaceholder,
  getNavLinks,
  allowGlobalReload = false,
}: Props) => {
  const history = useHistory();
  const {flagSettingsPage, flagUseNewOverviewPage} = useFeatureFlags();

  const navLinks = () => {
    return [
      {
        title: 'overview',
        element: (
          <ShortcutHandler
            key="overview"
            onShortcut={() => history.push('/overview')}
            shortcutLabel="⌥1"
            shortcutFilter={(e) => e.altKey && e.code === 'Digit1'}
          >
            <TopNavLink to="/overview" data-cy="AppTopNav_StatusLink">
              Overview
            </TopNavLink>
          </ShortcutHandler>
        ),
      },
      {
        title: 'runs',
        element: (
          <ShortcutHandler
            key="runs"
            onShortcut={() => history.push('/runs')}
            shortcutLabel="⌥2"
            shortcutFilter={(e) => e.altKey && e.code === 'Digit2'}
          >
            <TopNavLink to="/runs" data-cy="AppTopNav_RunsLink">
              Runs
            </TopNavLink>
          </ShortcutHandler>
        ),
      },
      {
        title: 'assets',
        element: (
          <ShortcutHandler
            key="assets"
            onShortcut={() => history.push('/assets')}
            shortcutLabel="⌥3"
            shortcutFilter={(e) => e.altKey && e.code === 'Digit3'}
          >
            <TopNavLink
              to={flagUseNewOverviewPage ? '/assets-overview' : '/assets'}
              data-cy="AppTopNav_AssetsLink"
              isActive={(_, location) => {
                const {pathname} = location;
                return pathname.startsWith('/assets') || pathname.startsWith('/asset-groups');
              }}
              exact={false}
            >
              Assets
            </TopNavLink>
          </ShortcutHandler>
        ),
      },
      flagSettingsPage
        ? {
            title: 'settings',
            element: (
              <ShortcutHandler
                key="settings"
                onShortcut={() => history.push('/settings')}
                shortcutLabel="⌥4"
                shortcutFilter={(e) => e.altKey && e.code === 'Digit4'}
              >
                <TopNavLink
                  to="/settings"
                  data-cy="AppTopNav_SettingsLink"
                  isActive={(_, location) => {
                    const {pathname} = location;
                    return pathname.startsWith('/settings') || pathname.startsWith('/locations');
                  }}
                >
                  <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
                    Settings
                    <DeploymentStatusIcon />
                  </Box>
                </TopNavLink>
              </ShortcutHandler>
            ),
          }
        : {
            title: 'deployment',
            element: (
              <ShortcutHandler
                key="deployment"
                onShortcut={() => history.push('/locations')}
                shortcutLabel="⌥4"
                shortcutFilter={(e) => e.altKey && e.code === 'Digit4'}
              >
                <TopNavLink
                  to="/locations"
                  data-cy="AppTopNav_StatusLink"
                  isActive={(_, location) => {
                    const {pathname} = location;
                    return (
                      pathname.startsWith('/locations') ||
                      pathname.startsWith('/health') ||
                      pathname.startsWith('/config')
                    );
                  }}
                >
                  <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
                    Deployment
                    <DeploymentStatusIcon />
                  </Box>
                </TopNavLink>
              </ShortcutHandler>
            ),
          },
    ];
  };

  const {reloading, tryReload} = useRepositoryLocationReload({
    scope: 'workspace',
    reloadFn: reloadFnForWorkspace,
  });

  return (
    <AppTopNavContainer>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
        <AppTopNavLogo />
        <Box margin={{left: 8}} flex={{direction: 'row', alignItems: 'center', gap: 16}}>
          {getNavLinks ? getNavLinks(navLinks()) : navLinks().map((link) => link.element)}
        </Box>
        {rightOfSearchBar}
      </Box>
      <Box flex={{direction: 'row', alignItems: 'center'}}>
        {allowGlobalReload ? (
          <ShortcutHandler
            onShortcut={() => {
              if (!reloading) {
                tryReload();
              }
            }}
            shortcutLabel={`⌥R - ${reloading ? 'Reloading' : 'Reload all code locations'}`}
            // On OSX Alt + R creates ®, not sure about windows, so checking 'r' for windows
            shortcutFilter={(e) => e.altKey && (e.key === '®' || e.key === 'r')}
          >
            <div style={{width: '0px', height: '30px'}} />
          </ShortcutHandler>
        ) : null}
        <SearchDialog searchPlaceholder={searchPlaceholder} />
        {children}
      </Box>
    </AppTopNavContainer>
  );
};

export const AppTopNavLogo = () => {
  const {nav} = React.useContext(LayoutContext);
  const navButton = React.useRef<null | HTMLButtonElement>(null);

  const onToggle = React.useCallback(() => {
    navButton.current && navButton.current.focus();
    nav.isOpen ? nav.close() : nav.open();
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

export const GhostDaggyWithTooltip = () => {
  return (
    <DaggyTooltip
      content={
        <Box flex={{direction: 'row', gap: 4}}>
          <WebSocketStatus />
          <VersionNumber />
        </Box>
      }
      placement="bottom"
      modifiers={{offset: {enabled: true, options: {offset: [0, 18]}}}}
    >
      <Link to="/home" style={{outline: 0, display: 'flex'}}>
        <GhostDaggy />
      </Link>
    </DaggyTooltip>
  );
};

const GhostDaggy = () => (
  <svg width="36" height="36" viewBox="0 0 255 255" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M85.3118 244.06C85.3159 245.476 85.6118 246.875 86.181 248.172C86.7501 249.468 87.5802 250.633 88.6196 251.594C89.6589 252.555 90.8851 253.291 92.2216 253.757C93.5581 254.222 94.9762 254.407 96.3874 254.3C150.026 250.46 200.686 212.5 216.86 153.21C217.71 149.8 220.268 148.09 223.677 148.09C225.425 148.16 227.074 148.917 228.268 150.195C229.461 151.474 230.103 153.171 230.055 154.92C230.055 168.14 213.061 202.69 188.761 222.74C187.522 223.782 186.535 225.09 185.872 226.567C185.209 228.044 184.888 229.652 184.932 231.27C184.957 232.586 185.241 233.884 185.768 235.09C186.296 236.296 187.055 237.385 188.005 238.297C188.954 239.208 190.073 239.923 191.299 240.401C192.525 240.878 193.833 241.109 195.148 241.08C197.278 241.08 200.686 239.8 204.945 235.96C221.938 220.6 254.325 177.52 254.325 130.17C254.325 60.75 200.656 0.929932 125.756 0.929932C58.9222 0.929932 1.02502 55.5299 1.02502 118.66C1.02502 160.46 34.2319 192.02 78.0746 192.02C111.711 192.02 142.789 168.14 151.306 135.29C152.155 131.88 154.704 130.17 158.113 130.17C159.861 130.24 161.512 130.996 162.707 132.275C163.902 133.553 164.547 135.25 164.501 137C164.501 151.93 136.402 204 79.3541 204C65.7295 204 48.7062 200.16 36.7809 193.33C35.1845 192.556 33.4455 192.12 31.6729 192.05C30.3157 191.998 28.9623 192.227 27.6979 192.724C26.4335 193.22 25.2855 193.973 24.326 194.934C23.3665 195.896 22.6163 197.046 22.1225 198.312C21.6288 199.578 21.4022 200.932 21.457 202.29C21.5121 204.029 22.0102 205.726 22.9041 207.218C23.798 208.711 25.058 209.951 26.5649 210.82C42.3187 219.82 61.0513 224.47 80.2038 224.47C127.885 224.47 171.308 192.05 184.083 144.28C184.932 140.87 187.491 139.16 190.89 139.16C192.638 139.23 194.289 139.986 195.484 141.264C196.679 142.543 197.324 144.24 197.278 145.99C197.278 165.61 162.371 228.74 95.1079 233.86C92.5054 234.053 90.066 235.201 88.2579 237.084C86.4499 238.966 85.4007 241.451 85.3118 244.06Z"
      fill="#DEDEFC"
    />
    <path
      d="M151.965 80.6999C161.146 80.6314 170.158 83.1697 177.955 88.0199C178.743 83.7059 179.178 79.3347 179.255 74.9499C179.255 54.6999 163.821 36.5599 145.028 36.5599C130.414 36.5599 121.277 48.6699 121.277 63.6299C121.208 71.7115 124.046 79.5486 129.274 85.7099C136.357 82.3314 144.119 80.6177 151.965 80.6999Z"
      fill="white"
    />
    <path
      d="M195.998 154.06C198.607 145.14 199.757 138.95 199.757 134.93C199.677 133.194 198.933 131.555 197.679 130.352C196.425 129.15 194.757 128.476 193.019 128.47C191.401 128.5 189.839 129.071 188.582 130.091C187.325 131.111 186.445 132.522 186.082 134.1C185.372 137.03 183.853 144.97 182.354 150.01C182.973 148.123 183.54 146.207 184.053 144.26C184.903 140.84 187.461 139.14 190.86 139.14C192.607 139.208 194.258 139.962 195.453 141.238C196.649 142.515 197.294 144.211 197.248 145.96C197.167 148.709 196.727 151.436 195.938 154.07L195.998 154.06Z"
      fill="#C9C6FA"
    />
    <path
      d="M232.184 144.74C232.102 143.007 231.359 141.37 230.107 140.169C228.856 138.967 227.191 138.291 225.456 138.28C223.84 138.312 222.28 138.884 221.025 139.904C219.77 140.924 218.892 142.334 218.529 143.91C217.809 146.91 216.26 154.97 214.741 160H214.811C215.55 157.76 216.24 155.49 216.81 153.18C217.659 149.76 220.218 148.06 223.627 148.06C225.374 148.128 227.023 148.882 228.217 150.159C229.411 151.436 230.053 153.132 230.005 154.88C229.956 157.003 229.664 159.113 229.135 161.17C231.254 153.73 232.184 148.35 232.184 144.74Z"
      fill="#C9C6FA"
    />
    <path
      d="M151.965 80.6999C156.528 80.6907 161.071 81.2996 165.47 82.5099C167.78 79.359 168.934 75.5083 168.738 71.6059C168.543 67.7035 167.009 63.9876 164.396 61.0835C161.783 58.1795 158.25 56.2646 154.391 55.6611C150.532 55.0576 146.583 55.8023 143.209 57.77L150.206 69.29L137.101 63.62C135.326 66.4853 134.436 69.8112 134.543 73.1805C134.65 76.5499 135.748 79.8127 137.701 82.5599C142.352 81.3061 147.149 80.6805 151.965 80.6999Z"
      fill="#163B36"
    />
    <path
      d="M51.0052 154.84C56.5259 154.84 61.0013 150.363 61.0013 144.84C61.0013 139.317 56.5259 134.84 51.0052 134.84C45.4845 134.84 41.0092 139.317 41.0092 144.84C41.0092 150.363 45.4845 154.84 51.0052 154.84Z"
      fill="#C9C6FA"
    />
    <path
      d="M51.0052 114.84C56.5259 114.84 61.0013 110.363 61.0013 104.84C61.0013 99.317 56.5259 94.8398 51.0052 94.8398C45.4845 94.8398 41.0092 99.317 41.0092 104.84C41.0092 110.363 45.4845 114.84 51.0052 114.84Z"
      fill="#C9C6FA"
    />
    <path
      d="M31.0131 134.84C36.5338 134.84 41.0092 130.363 41.0092 124.84C41.0092 119.317 36.5338 114.84 31.0131 114.84C25.4925 114.84 21.0171 119.317 21.0171 124.84C21.0171 130.363 25.4925 134.84 31.0131 134.84Z"
      fill="#C9C6FA"
    />
    <path
      d="M75.9954 192H77.9946C111.631 192 142.709 168.12 151.226 135.27C152.075 131.86 154.624 130.15 158.033 130.15C159.781 130.22 161.432 130.976 162.627 132.255C163.822 133.533 164.467 135.23 164.421 136.98C164.268 140.47 163.479 143.904 162.091 147.11C162.333 146.738 162.543 146.346 162.721 145.94C165.25 140.157 166.557 133.913 166.56 127.6C166.56 117.79 159.742 111.39 149.956 111.39C132.893 111.39 129.474 126.29 122.277 142.22C114.81 158.76 101.096 176.65 66.5092 176.65C30.5734 176.65 -6.35207 151.48 2.65438 100.3C2.76433 99.66 2.85429 99.0899 2.92426 98.5599C1.60457 105.172 0.934978 111.897 0.925049 118.64C1.02501 159.84 33.2023 191.04 75.9954 192Z"
      fill="#C9C6FA"
    />
  </svg>
);

const DaggyTooltip = styled(Tooltip)`
  &.bp4-popover2-target {
    display: inline-flex;
  }
`;

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
