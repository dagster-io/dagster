import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {useHistory, Link, useRouteMatch} from 'react-router-dom';
import styled from 'styled-components/macro';

import {LayoutContext} from '../app/LayoutProvider';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';

import {InstanceWarningIcon} from './InstanceWarningIcon';
import {LeftNavRepositorySection} from './LeftNavRepositorySection';
import {WorkspaceWarningIcon} from './WorkspaceWarningIcon';

export const LeftNav = () => {
  const history = useHistory();
  const {nav} = React.useContext(LayoutContext);

  const runsMatch = useRouteMatch('/instance/runs');
  const assetsMatch = useRouteMatch('/instance/assets');
  const statusMatch = useRouteMatch([
    '/instance/health',
    '/instance/schedules',
    '/instance/sensors',
    '/instance/config',
  ]);
  const workspaceMatch = useRouteMatch({path: '/workspace', exact: true});

  return (
    <LeftNavContainer $open={nav.isOpen}>
      <Box padding={{top: 4}}>
        <Box padding={{horizontal: 12}} margin={{bottom: 4}}>
          <div
            style={{
              fontSize: 10.5,
              color: ColorsWIP.Gray400,
              userSelect: 'none',
              textTransform: 'uppercase',
            }}
          >
            Instance
          </div>
        </Box>
        <ShortcutHandler
          onShortcut={() => history.push('/instance/runs')}
          shortcutLabel={`⌥1`}
          shortcutFilter={(e) => e.code === 'Digit1' && e.altKey}
        >
          <Tab to="/instance/runs" className={!!runsMatch ? 'selected' : ''}>
            <IconWIP name="settings_backup_restore" color={ColorsWIP.White} />
            <TabLabel>Runs</TabLabel>
          </Tab>
        </ShortcutHandler>
        <ShortcutHandler
          onShortcut={() => history.push('/instance/assets')}
          shortcutLabel={`⌥2`}
          shortcutFilter={(e) => e.code === 'Digit2' && e.altKey}
        >
          <Tab to="/instance/assets" className={!!assetsMatch ? 'selected' : ''}>
            <IconWIP name="table_view" color={ColorsWIP.White} />
            <TabLabel>Assets</TabLabel>
          </Tab>
        </ShortcutHandler>
        <ShortcutHandler
          onShortcut={() => history.push('/instance')}
          shortcutLabel={`⌥3`}
          shortcutFilter={(e) => e.code === 'Digit3' && e.altKey}
        >
          <Tab to="/instance" className={!!statusMatch ? 'selected' : ''}>
            <IconWIP name="speed" color={ColorsWIP.White} />
            <TabLabel>Status</TabLabel>
            <InstanceWarningIcon />
          </Tab>
        </ShortcutHandler>
        <ShortcutHandler
          onShortcut={() => history.push('/workspace')}
          shortcutLabel={`⌥4`}
          shortcutFilter={(e) => e.code === 'Digit4' && e.altKey}
        >
          <Tab to="/workspace" className={!!workspaceMatch ? 'selected' : ''}>
            <IconWIP name="source" color={ColorsWIP.White} />
            <TabLabel>Workspace</TabLabel>
            <WorkspaceWarningIcon />
          </Tab>
        </ShortcutHandler>
      </Box>
      <LeftNavRepositorySection />
    </LeftNavContainer>
  );
};

const LeftNavContainer = styled.div<{$open: boolean}>`
  position: fixed;
  z-index: 2;
  top: 48px;
  bottom: 0;
  left: 0;
  width: 280px;
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  justify-content: start;
  background: ${Colors.DARK_GRAY2};
  border-right: 1px solid ${Colors.DARK_GRAY5};

  @media (max-width: 1440px) {
    box-shadow: 2px 0px 0px ${Colors.LIGHT_GRAY1};
    transform: translateX(${({$open}) => ($open ? '0' : '-280px')});
    transition: transform 150ms ease-in-out;
  }
`;

const Tab = styled(Link)`
  color: ${Colors.LIGHT_GRAY1} !important;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  display: flex;
  padding: 8px 10px;
  align-items: center;
  outline: 0;
  &:hover {
    color: ${Colors.WHITE} !important;
    text-decoration: none;
  }
  &:focus {
    outline: 0;
  }
  &.selected {
    color: ${Colors.WHITE} !important;
    border-left: 4px solid ${Colors.COBALT3};
    font-weight: 600;
  }
`;

const TabLabel = styled.div`
  font-size: 13px;
  margin-left: 8px;
  text-decoration: none;
  white-space: nowrap;
  text-decoration: none;
`;
