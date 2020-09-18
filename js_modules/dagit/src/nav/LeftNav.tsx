import {Colors, Icon} from '@blueprintjs/core';
import * as React from 'react';
import {useHistory, useRouteMatch} from 'react-router';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {DagsterRepoOption} from '../DagsterRepositoryContext';
import {ShortcutHandler} from '../ShortcutHandler';
import {TimezonePicker} from '../TimeComponents';
import {WebsocketStatus} from '../WebsocketStatus';
import navBarImage from '../images/nav-logo-icon.png';
import navTitleImage from '../images/nav-title.png';

import {InstanceDetailsLink} from './InstanceDetailsLink';
import {RepositoryContentList} from './RepositoryContentList';
import {RepositoryPicker} from './RepositoryPicker';
import {SchedulesList} from './SchedulesList';

const KEYCODE_FOR_1 = 49;

const INSTANCE_TABS = [
  {
    to: `/runs`,
    tab: `runs`,
    icon: <Icon icon="history" iconSize={18} />,
    label: 'Runs',
  },
  {
    to: `/assets`,
    tab: `assets`,
    icon: <Icon icon="panel-table" iconSize={18} />,
    label: 'Assets',
  },
  {
    to: `/scheduler`,
    tab: `scheduler`,
    icon: <Icon icon="time" iconSize={18} />,
    label: 'Scheduler',
  },
];

interface LeftNavProps {
  options: DagsterRepoOption[];
  repo: DagsterRepoOption | null;
  setRepo: (repo: DagsterRepoOption) => void;
}

export const LeftNav: React.FunctionComponent<LeftNavProps> = ({options, repo, setRepo}) => {
  const history = useHistory();
  const match = useRouteMatch<
    | {selector: string; tab: string; rootTab: undefined}
    | {selector: undefined; tab: undefined; rootTab: string}
  >(['/pipeline/:selector/:tab?', '/solid/:selector', '/schedules/:selector', '/:rootTab?']);

  return (
    <LeftNavContainer>
      <div>
        <LogoContainer>
          <img
            alt="logo"
            src={navBarImage}
            style={{height: 40}}
            onClick={() => history.push('/')}
          />
          <LogoMetaContainer>
            <img src={navTitleImage} style={{height: 10}} alt="title" />
            <InstanceDetailsLink />
          </LogoMetaContainer>
          <LogoWebsocketStatus />
        </LogoContainer>
        {INSTANCE_TABS.map((t, i) => (
          <ShortcutHandler
            key={t.tab}
            onShortcut={() => history.push(t.to)}
            shortcutLabel={`⌥${i + 1}`}
            shortcutFilter={(e) => e.keyCode === KEYCODE_FOR_1 + i && e.altKey}
          >
            <Tab to={t.to} className={match?.params.rootTab === t.tab ? 'selected' : ''}>
              {t.icon}
              <TabLabel>{t.label}</TabLabel>
            </Tab>
          </ShortcutHandler>
        ))}
      </div>
      <div style={{height: 20}} />
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
        <RepositoryPicker options={options} repo={repo} setRepo={setRepo} />
        {repo && (
          <div style={{display: 'flex', flex: 1, flexDirection: 'column', minHeight: 0}}>
            <ItemHeader>Pipelines & Solids:</ItemHeader>
            <RepositoryContentList {...match?.params} repo={repo} />
            <ItemHeader>Schedules:</ItemHeader>
            <SchedulesList {...match?.params} repo={repo} />
          </div>
        )}
      </div>
      <TimezonePicker />
    </LeftNavContainer>
  );
};

const LogoWebsocketStatus = styled(WebsocketStatus)`
  position: absolute;
  top: 28px;
  left: 42px;
`;

const ItemHeader = styled.div`
  font-size: 15px;
  text-overflow: ellipsis;
  overflow: hidden;
  padding: 8px 12px;
  padding-left: 8px;
  margin-top: 10px;
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
  padding-top: 14px;
`;

const Tab = styled(Link)`
  color: ${Colors.LIGHT_GRAY1} !important;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  display: flex;
  padding: 8px 12px;
  margin: 0px 0;
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
  margin-left: 6px;
  text-decoration: none;
  white-space: nowrap;
  text-decoration: none;
`;

const LogoContainer = styled.div`
  width: 100%;
  padding: 0 10px;
  margin-bottom: 10px;
  position: relative;
  cursor: pointer;
  &:hover {
    img {
      filter: brightness(110%);
    }
  }
`;

const LogoMetaContainer = styled.div`
  position: absolute;
  left: 56px;
  top: -3px;
  height: 42px;
  padding-left: 4px;
  right: 0;
  z-index: 1;
  border-bottom: 1px solid ${Colors.DARK_GRAY4};
`;
