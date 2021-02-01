import {ApolloConsumer} from '@apollo/client';
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
import {InstanceDetailsLink} from 'src/nav/InstanceDetailsLink';
import {JobsList} from 'src/nav/JobsList';
import {RepositoryContentList} from 'src/nav/RepositoryContentList';
import {RepositoryLocationStateObserver} from 'src/nav/RepositoryLocationStateObserver';
import {RepositoryPicker} from 'src/nav/RepositoryPicker';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Caption} from 'src/ui/Text';
import {WorkspaceContext} from 'src/workspace/WorkspaceContext';

const KEYCODE_FOR_1 = 49;

const INSTANCE_TABS = [
  {
    to: `/instance/runs`,
    tab: `runs`,
    icon: <Icon icon="history" iconSize={16} />,
    label: 'Runs',
  },
  {
    to: `/instance/assets`,
    tab: `assets`,
    icon: <Icon icon="panel-table" iconSize={16} />,
    label: 'Assets',
  },
  {
    to: `/instance`,
    tab: `instance-status`,
    icon: <Icon icon="dashboard" iconSize={16} />,
    label: 'Status',
  },
];

const LeftNavRepositorySection = () => {
  const match = useRouteMatch<
    | {repoPath: string; selector: string; tab: string; rootTab: undefined}
    | {selector: undefined; tab: undefined; rootTab: string}
  >([
    '/workspace/:repoPath/pipelines/:selector/:tab?',
    '/workspace/:repoPath/solids/:selector',
    '/workspace/:repoPath/schedules/:selector',
    '/:rootTab?',
  ]);

  const {activeRepo, allRepos, loading, locations} = React.useContext(WorkspaceContext);

  const anyErrors = locations.some((node) => node.__typename === 'RepositoryLocationLoadFailure');

  return (
    <div
      className="bp3-dark"
      style={{
        background: `rgba(0,0,0,0.3)`,
        color: Colors.WHITE,
        display: 'flex',
        flex: 1,
        overflow: 'none',
        flexDirection: 'column',
        minHeight: 0,
      }}
    >
      <RepositoryPicker loading={loading} options={allRepos} repo={activeRepo?.repo || null} />
      <ApolloConsumer>
        {(client) => <RepositoryLocationStateObserver client={client} />}
      </ApolloConsumer>
      {anyErrors ? (
        <Group
          background={Colors.GOLD5}
          padding={{vertical: 8, horizontal: 12}}
          direction="row"
          spacing={8}
        >
          <Icon icon="warning-sign" color={Colors.DARK_GRAY3} iconSize={14} />
          <Caption color={Colors.DARK_GRAY3}>
            An error occurred while loading a repository.{' '}
            <DetailLink to="/instance/health#repository-locations">View details</DetailLink>
          </Caption>
        </Group>
      ) : null}
      {activeRepo ? (
        <div style={{display: 'flex', flex: 1, flexDirection: 'column', minHeight: 0}}>
          <ItemHeader>{'Pipelines & Solids:'}</ItemHeader>
          <RepositoryContentList {...match?.params} repo={activeRepo.repo} />
          <ItemHeader>{`Schedules & Sensors:`}</ItemHeader>
          <JobsList {...match?.params} repo={activeRepo.repo} />
        </div>
      ) : null}
    </div>
  );
};

export const LeftNav = () => {
  const history = useHistory();
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
              <InstanceDetailsLink />
            </div>
          </Group>
        </LogoContainer>
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
        {INSTANCE_TABS.map((t, i) => (
          <ShortcutHandler
            key={t.tab}
            onShortcut={() => history.push(t.to)}
            shortcutLabel={`⌥${i + 1}`}
            shortcutFilter={(e) => e.keyCode === KEYCODE_FOR_1 + i && e.altKey}
          >
            <Tab to={t.to}>
              {t.icon}
              <TabLabel>{t.label}</TabLabel>
            </Tab>
          </ShortcutHandler>
        ))}
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

const ItemHeader = styled.div`
  font-size: 15px;
  text-overflow: ellipsis;
  overflow: hidden;
  padding: 8px 12px 8px 8px;
  border-left: 4px solid transparent;
  border-bottom: 1px solid transparent;
  display: block;
  font-weight: bold;
  color: ${Colors.LIGHT_GRAY3} !important;
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

const DetailLink = styled(Link)`
  color: ${Colors.DARK_GRAY3};
  text-decoration: underline;

  && :hover,
  :active,
  :visited {
    color: ${Colors.DARK_GRAY1};
  }
`;
