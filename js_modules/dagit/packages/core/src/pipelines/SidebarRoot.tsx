import {gql} from '@apollo/client';
import {Box, Colors, Tabs} from '@dagster-io/ui';
import * as React from 'react';

import {OpNameOrPath} from '../ops/OpNameOrPath';
import {TypeExplorerContainer} from '../typeexplorer/TypeExplorerContainer';
import {TypeListContainer} from '../typeexplorer/TypeListContainer';
import {TabLink} from '../ui/TabLink';
import {RepoAddress} from '../workspace/types';

import {RightInfoPanelContent} from './GraphExplorer';
import {GraphExplorerJobContext} from './GraphExplorerJobContext';
import {ExplorerPath} from './PipelinePathUtils';
import {SidebarOpContainer} from './SidebarOpContainer';
import {SidebarOpContainerInfo, SIDEBAR_OP_CONTAINER_INFO_FRAGMENT} from './SidebarPipelineInfo';
import {SidebarRootContainerFragment} from './types/SidebarRootContainerFragment';

type TabKey = 'types' | 'info';

interface TabDefinition {
  name: string;
  key: TabKey;
  content: () => React.ReactNode;
}

interface SidebarRootProps {
  tab?: TabKey;
  typeName?: string;
  container: SidebarRootContainerFragment;
  explorerPath: ExplorerPath;
  opHandleID?: string;
  parentOpHandleID?: string;
  getInvocations?: (definitionName: string) => {handleID: string}[];
  onEnterSubgraph: (arg: OpNameOrPath) => void;
  onClickOp: (arg: OpNameOrPath) => void;
  repoAddress?: RepoAddress;
  isGraph: boolean;
}

export const SidebarRoot: React.FC<SidebarRootProps> = (props) => {
  const {
    tab,
    typeName,
    container,
    explorerPath,
    opHandleID,
    getInvocations,
    parentOpHandleID,
    onEnterSubgraph,
    onClickOp,
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
        opHandleID ? (
          <SidebarOpContainer
            key={opHandleID}
            explorerPath={explorerPath}
            handleID={opHandleID}
            showingSubgraph={false}
            getInvocations={getInvocations}
            onEnterSubgraph={onEnterSubgraph}
            onClickOp={onClickOp}
            repoAddress={repoAddress}
            isGraph={isGraph}
          />
        ) : parentOpHandleID ? (
          <SidebarOpContainer
            key={parentOpHandleID}
            explorerPath={explorerPath}
            handleID={parentOpHandleID}
            showingSubgraph={true}
            getInvocations={getInvocations}
            onClickOp={onClickOp}
            repoAddress={repoAddress}
            isGraph={isGraph}
          />
        ) : jobContext ? (
          jobContext.sidebarTab
        ) : (
          <SidebarOpContainerInfo isGraph={isGraph} container={container} key={container.name} />
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
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <Tabs selectedTabId={activeTab}>
          {TabDefinitions.map(({name, key}) => (
            <TabLink id={key} key={key} to={{search: `?tab=${key}`}} title={name} />
          ))}
        </Tabs>
      </Box>
      <RightInfoPanelContent>
        {TabDefinitions.find((t) => t.key === activeTab)?.content()}
      </RightInfoPanelContent>
    </>
  );
};

export const SIDEBAR_ROOT_CONTAINER_FRAGMENT = gql`
  fragment SidebarRootContainerFragment on SolidContainer {
    id
    name
    ...SidebarOpContainerInfoFragment
  }

  ${SIDEBAR_OP_CONTAINER_INFO_FRAGMENT}
`;
