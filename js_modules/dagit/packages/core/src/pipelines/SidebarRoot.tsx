import {Box, Colors, Tabs} from '@dagster-io/ui';
import * as React from 'react';

import {OpNameOrPath} from '../ops/OpNameOrPath';
import {TypeExplorerContainer} from '../typeexplorer/TypeExplorerContainer';
import {TypeListContainer} from '../typeexplorer/TypeListContainer';
import {TabLink} from '../ui/TabLink';
import {RepoAddress} from '../workspace/types';

import {RightInfoPanelContent} from './GraphExplorer';
import {ExplorerPath} from './PipelinePathUtils';
import {SidebarContainerOverview} from './SidebarContainerOverview';
import {SidebarOp} from './SidebarOp';
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
}

export const SidebarRoot: React.FC<SidebarRootProps> = (props) => {
  const {
    tab,
    typeName,
    container,
    repoAddress,
    explorerPath,
    opHandleID,
    getInvocations,
    parentOpHandleID,
    onEnterSubgraph,
    onClickOp,
  } = props;

  const activeTab = tab || 'info';

  const TabDefinitions: Array<TabDefinition> = [
    {
      name: 'Info',
      key: 'info',
      content: () =>
        opHandleID ? (
          <SidebarOp
            key={opHandleID}
            explorerPath={explorerPath}
            handleID={opHandleID}
            showingSubgraph={false}
            getInvocations={getInvocations}
            onEnterSubgraph={onEnterSubgraph}
            onClickOp={onClickOp}
            repoAddress={repoAddress}
            isGraph={container.__typename === 'Graph'}
          />
        ) : parentOpHandleID ? (
          <SidebarOp
            key={parentOpHandleID}
            explorerPath={explorerPath}
            handleID={parentOpHandleID}
            showingSubgraph={true}
            getInvocations={getInvocations}
            onClickOp={onClickOp}
            repoAddress={repoAddress}
            isGraph={container.__typename === 'Graph'}
          />
        ) : (
          <SidebarContainerOverview repoAddress={repoAddress} container={container} />
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
