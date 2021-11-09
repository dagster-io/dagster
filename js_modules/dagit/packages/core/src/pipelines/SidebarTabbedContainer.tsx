import {gql} from '@apollo/client';
import * as React from 'react';

import {SolidNameOrPath} from '../solids/SolidNameOrPath';
import {TypeExplorerContainer} from '../typeexplorer/TypeExplorerContainer';
import {TypeListContainer} from '../typeexplorer/TypeListContainer';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Tab, Tabs} from '../ui/Tabs';
import {RepoAddress} from '../workspace/types';

import {GraphExplorerJobContext} from './GraphExplorerJobContext';
import {ExplorerPath} from './PipelinePathUtils';
import {
  SidebarSolidContainerInfo,
  SIDEBAR_SOLID_CONTAINER_INFO_FRAGMENT,
} from './SidebarPipelineInfo';
import {SidebarSolidContainer} from './SidebarSolidContainer';
import {SidebarTabbedContainerPipelineFragment} from './types/SidebarTabbedContainerPipelineFragment';

type TabKey = 'types' | 'info';

interface TabDefinition {
  name: string;
  key: TabKey;
  content: () => React.ReactNode;
}

interface ISidebarTabbedContainerProps {
  tab?: TabKey;
  typeName?: string;
  pipeline: SidebarTabbedContainerPipelineFragment;
  explorerPath: ExplorerPath;
  solidHandleID?: string;
  parentSolidHandleID?: string;
  getInvocations?: (definitionName: string) => {handleID: string}[];
  onEnterCompositeSolid: (arg: SolidNameOrPath) => void;
  onClickSolid: (arg: SolidNameOrPath) => void;
  repoAddress?: RepoAddress;
  isGraph: boolean;
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
    isGraph,
  } = props;

  const jobContext = React.useContext(GraphExplorerJobContext);

  const activeTab = tab || 'info';

  const TabDefinitions: Array<TabDefinition> = [
    {
      name: 'Info',
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
            isGraph={isGraph}
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
            isGraph={isGraph}
          />
        ) : jobContext ? (
          jobContext.sidebarTab
        ) : (
          <SidebarSolidContainerInfo isGraph={!!isGraph} pipeline={pipeline} key={pipeline.name} />
        ),
    },
    {
      name: 'Types',
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
      <Box
        padding={{horizontal: 24}}
        border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
      >
        <Tabs selectedTabId={activeTab}>
          {TabDefinitions.map(({name, key}) => (
            <Tab id={key} key={key} to={{search: `?tab=${key}`}} title={name} />
          ))}
        </Tabs>
      </Box>
      {TabDefinitions.find((t) => t.key === activeTab)?.content()}
    </>
  );
};

export const SIDEBAR_TABBED_CONTAINER_PIPELINE_FRAGMENT = gql`
  fragment SidebarTabbedContainerPipelineFragment on SolidContainer {
    id
    name
    ...SidebarSolidContainerInfoFragment
  }

  ${SIDEBAR_SOLID_CONTAINER_INFO_FRAGMENT}
`;
