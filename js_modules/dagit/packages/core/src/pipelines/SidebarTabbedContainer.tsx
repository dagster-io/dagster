import {gql} from '@apollo/client';
import {Colors, Icon, IconName} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {SolidNameOrPath} from '../solids/SolidNameOrPath';
import {TypeExplorerContainer} from '../typeexplorer/TypeExplorerContainer';
import {TypeListContainer} from '../typeexplorer/TypeListContainer';
import {RepoAddress} from '../workspace/types';

import {PipelineExplorerPath} from './PipelinePathUtils';
import {SidebarPipelineInfo, SIDEBAR_PIPELINE_INFO_FRAGMENT} from './SidebarPipelineInfo';
import {SidebarSolidContainer} from './SidebarSolidContainer';
import {SidebarTabbedContainerPipelineFragment} from './types/SidebarTabbedContainerPipelineFragment';

interface ISidebarTabbedContainerProps {
  types?: string;
  typeExplorer?: string;
  pipeline: SidebarTabbedContainerPipelineFragment;
  explorerPath: PipelineExplorerPath;
  solidHandleID?: string;
  parentSolidHandleID?: string;
  getInvocations?: (definitionName: string) => {handleID: string}[];
  onEnterCompositeSolid: (arg: SolidNameOrPath) => void;
  onClickSolid: (arg: SolidNameOrPath) => void;
  repoAddress?: RepoAddress;
}

interface ITabInfo {
  name: string;
  icon: IconName;
  key: string;
  link: string;
}

const TabInfo: Array<ITabInfo> = [
  {
    name: 'Info',
    icon: 'data-lineage',
    key: 'info',
    link: '?',
  },
  {
    name: 'Types',
    icon: 'manual',
    key: 'types',
    link: '?types=true',
  },
];

export const SidebarTabbedContainer: React.FC<ISidebarTabbedContainerProps> = (props) => {
  const {
    typeExplorer,
    types,
    pipeline,
    explorerPath,
    solidHandleID,
    getInvocations,
    parentSolidHandleID,
    onEnterCompositeSolid,
    onClickSolid,
    repoAddress,
  } = props;

  let content = <div />;
  let activeTab = 'info';

  if (typeExplorer) {
    activeTab = 'types';
    content = (
      <TypeExplorerContainer
        explorerPath={explorerPath}
        repoAddress={repoAddress}
        typeName={typeExplorer}
      />
    );
  } else if (types) {
    activeTab = 'types';
    content = <TypeListContainer repoAddress={repoAddress} explorerPath={explorerPath} />;
  } else if (solidHandleID) {
    content = (
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
    );
  } else if (parentSolidHandleID) {
    content = (
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
    );
  } else {
    content = (
      <SidebarPipelineInfo
        pipeline={pipeline}
        mode={explorerPath.pipelineMode}
        key={pipeline.name}
      />
    );
  }

  return (
    <>
      <Tabs>
        {TabInfo.map(({name, icon, key, link}) => (
          <Link to={link} key={key}>
            <Tab key={key} active={key === activeTab}>
              <Icon icon={icon} style={{marginRight: 8}} />
              {name}
            </Tab>
          </Link>
        ))}
      </Tabs>
      {content}
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

const Tabs = styled.div`
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
`;
