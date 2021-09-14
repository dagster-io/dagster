import {gql} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {SolidNameOrPath} from '../solids/SolidNameOrPath';
import {TypeExplorerContainer} from '../typeexplorer/TypeExplorerContainer';
import {TypeListContainer} from '../typeexplorer/TypeListContainer';
import {Group} from '../ui/Group';
import {IconName, IconWIP} from '../ui/Icon';
import {RepoAddress} from '../workspace/types';

import {PipelineExplorerJobContext} from './PipelineExplorerJobContext';
import {PipelineExplorerPath} from './PipelinePathUtils';
import {SidebarPipelineInfo, SIDEBAR_PIPELINE_INFO_FRAGMENT} from './SidebarPipelineInfo';
import {SidebarSolidContainer} from './SidebarSolidContainer';
import {SidebarTabbedContainerPipelineFragment} from './types/SidebarTabbedContainerPipelineFragment';

type TabKey = 'types' | 'info';

interface TabDefinition {
  name: string;
  icon: IconName;
  key: TabKey;
  content: () => React.ReactNode;
}

interface ISidebarTabbedContainerProps {
  tab?: TabKey;
  typeName?: string;
  pipeline: SidebarTabbedContainerPipelineFragment;
  explorerPath: PipelineExplorerPath;
  solidHandleID?: string;
  parentSolidHandleID?: string;
  getInvocations?: (definitionName: string) => {handleID: string}[];
  onEnterCompositeSolid: (arg: SolidNameOrPath) => void;
  onClickSolid: (arg: SolidNameOrPath) => void;
  repoAddress?: RepoAddress;
}

export const SidebarTabbedContainer: React.FC<ISidebarTabbedContainerProps> = (props) => {
  const {
    tab,
    typeName,
    pipeline,
    explorerPath,
    solidHandleID,
    getInvocations,
    parentSolidHandleID,
    onEnterCompositeSolid,
    onClickSolid,
    repoAddress,
  } = props;

  const jobContext = React.useContext(PipelineExplorerJobContext);

  const activeTab = tab || 'info';

  const TabDefinitions: Array<TabDefinition> = [
    {
      name: 'Info',
      icon: 'schema',
      key: 'info',
      content: () =>
        solidHandleID ? (
          <SidebarSolidContainer
            key={solidHandleID}
            explorerPath={explorerPath}
            handleID={solidHandleID}
            showingSubsolids={false}
            getInvocations={getInvocations}
            onEnterCompositeSolid={onEnterCompositeSolid}
            onClickSolid={onClickSolid}
            repoAddress={repoAddress}
          />
        ) : parentSolidHandleID ? (
          <SidebarSolidContainer
            key={parentSolidHandleID}
            explorerPath={explorerPath}
            handleID={parentSolidHandleID}
            showingSubsolids={true}
            getInvocations={getInvocations}
            onEnterCompositeSolid={onEnterCompositeSolid}
            onClickSolid={onClickSolid}
            repoAddress={repoAddress}
          />
        ) : jobContext ? (
          jobContext.sidebarTab
        ) : (
          <SidebarPipelineInfo pipeline={pipeline} key={pipeline.name} />
        ),
    },
    {
      name: 'Types',
      icon: 'menu_book',
      key: 'types',
      content: () =>
        typeName ? (
          <TypeExplorerContainer
            explorerPath={explorerPath}
            repoAddress={repoAddress}
            typeName={typeName}
          />
        ) : (
          <TypeListContainer repoAddress={repoAddress} explorerPath={explorerPath} />
        ),
    },
  ];

  return (
    <>
      <TabContainer>
        {TabDefinitions.map(({name, icon, key}) => (
          <Tab key={key} active={key === activeTab}>
            <Link to={{search: `?tab=${key}`}} key={key}>
              <Group direction="row" spacing={8} alignItems="center">
                <IconWIP name={icon} color={Colors.BLUE3} />
                {name}
              </Group>
            </Link>
          </Tab>
        ))}
      </TabContainer>
      {TabDefinitions.find((t) => t.key === activeTab)?.content()}
    </>
  );
};

export const SIDEBAR_TABBED_CONTAINER_PIPELINE_FRAGMENT = gql`
  fragment SidebarTabbedContainerPipelineFragment on IPipelineSnapshot {
    name
    ...SidebarPipelineInfoFragment
  }

  ${SIDEBAR_PIPELINE_INFO_FRAGMENT}
`;

const TabContainer = styled.div`
  width: 100%;
  display: flex;
  margin-top: 10px;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #ccc;
`;

const Tab = styled.div<{active: boolean}>`
  color: ${(p) => (p.active ? Colors.BLUE3 : Colors.GRAY2)}
  border-top: 3px solid transparent;
  border-bottom: 3px solid ${(p) => (p.active ? Colors.BLUE3 : 'transparent')};
  text-decoration: none;
  white-space: nowrap;
  min-width: 40px;
  padding: 0 10px;
  display: flex;
  height: 36px;
  align-items: center;

  :hover > * {
    text-decoration: none;
  }
`;
