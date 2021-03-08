import {Colors, Icon} from '@blueprintjs/core';
import * as React from 'react';
import {useHistory} from 'react-router';
import {Link, useRouteMatch} from 'react-router-dom';
import styled from 'styled-components/macro';

import {ShortcutHandler} from 'src/app/ShortcutHandler';
import {WebsocketStatus} from 'src/app/WebsocketStatus';
import {DarkTimezonePicker} from 'src/app/time/DarkTimezonePicker';
import navBarImage from 'src/images/nav-logo-icon.png';
import navTitleImage from 'src/images/nav-title.png';
import {InstanceWarningIcon} from 'src/nav/InstanceWarningIcon';
import {LeftNavRepositorySection} from 'src/nav/LeftNavRepositorySection';
import {VersionNumber} from 'src/nav/VersionNumber';
import {SearchDialog} from 'src/search/SearchDialog';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';

export const LeftNav = () => {
  const history = useHistory();
  const runsMatch = useRouteMatch('/instance/runs');
  const assetsMatch = useRouteMatch('/instance/assets');
  const statusMatch = useRouteMatch([
    '/instance/health',
    '/instance/schedules',
    '/instance/sensors',
    '/instance/config',
  ]);

  return (
    <LeftNavContainer>
      <Box padding={{vertical: 8}}>
        <LogoContainer>
          <Group direction="row" spacing={16} padding={{horizontal: 12}} margin={{bottom: 8}}>
            <div style={{position: 'relative'}}>
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
        <Box padding={{bottom: 8, horizontal: 12}}>
          <SearchDialog theme="dark" />
        </Box>
        <Box padding={{horizontal: 12}} margin={{bottom: 4}}>
          <div
            style={{
              fontSize: 10.5,
              color: Colors.GRAY1,
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
            <Icon icon="history" iconSize={16} />
            <TabLabel>Runs</TabLabel>
          </Tab>
        </ShortcutHandler>
        <ShortcutHandler
          onShortcut={() => history.push('/instance/assets')}
          shortcutLabel={`⌥2`}
          shortcutFilter={(e) => e.code === 'Digit2' && e.altKey}
        >
          <Tab to="/instance/assets" className={!!assetsMatch ? 'selected' : ''}>
            <Icon icon="panel-table" iconSize={16} />
            <TabLabel>Assets</TabLabel>
          </Tab>
        </ShortcutHandler>
        <ShortcutHandler
          onShortcut={() => history.push('/instance')}
          shortcutLabel={`⌥3`}
          shortcutFilter={(e) => e.code === 'Digit3' && e.altKey}
        >
          <Tab to="/instance" className={!!statusMatch ? 'selected' : ''}>
            <Icon icon="dashboard" iconSize={16} />
            <TabLabel>Status</TabLabel>
            <Box margin={{left: 8}}>
              <InstanceWarningIcon />
            </Box>
          </Tab>
        </ShortcutHandler>
      </Box>
      <LeftNavRepositorySection />
      <DarkTimezonePicker />
    </LeftNavContainer>
  );
};

const LogoWebsocketStatus = styled(WebsocketStatus)`
  position: absolute;
  top: 20px;
  left: 24px;
`;

const LeftNavContainer = styled.div`
  width: 235px;
  height: 100%;
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  justify-content: start;
  background: ${Colors.DARK_GRAY2};
  border-right: 1px solid ${Colors.DARK_GRAY5};
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

const LogoContainer = styled.div`
  cursor: pointer;
  &:hover {
    img {
      filter: brightness(110%);
    }
  }
`;
