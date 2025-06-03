import {Box, ErrorBoundary, Tabs} from '@dagster-io/ui-components';
import {useJobSidebarAlertsTabConfig} from 'shared/pipelines/useJobSidebarAlertsTabConfig.oss';

import {RightInfoPanelContent} from './GraphExplorer';
import {ExplorerPath} from './PipelinePathUtils';
import {SidebarContainerOverview} from './SidebarContainerOverview';
import {SidebarOp} from './SidebarOp';
import {TabDefinition, TabKey} from './types';
import {SidebarRootContainerFragment} from './types/SidebarContainerOverview.types';
import {OpNameOrPath} from '../ops/OpNameOrPath';
import {TypeExplorerContainer} from '../typeexplorer/TypeExplorerContainer';
import {TypeListContainer} from '../typeexplorer/TypeListContainer';
import {TabLink} from '../ui/TabLink';
import {RepoAddress} from '../workspace/types';

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
  isExternal?: boolean;
}

export const SidebarRoot = (props: SidebarRootProps) => {
  const {
    tab,
    typeName,
    container,
    repoAddress,
    explorerPath,
    opHandleID,
    getInvocations,
    isExternal,
    parentOpHandleID,
    onEnterSubgraph,
    onClickOp,
  } = props;

  const activeTab = tab || 'info';

  const tabDefinitions: TabDefinition[] = [
    {
      name: 'Info',
      key: 'info' as const,
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
    isExternal
      ? null
      : {
          name: 'Types',
          key: 'types' as const,
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
    useJobSidebarAlertsTabConfig({repoAddress, jobName: container.name}),
  ].filter((tab) => tab !== null);

  return (
    <>
      <Box padding={{horizontal: 24}} border="bottom">
        <Tabs selectedTabId={activeTab}>
          {tabDefinitions.map(({name, key}) => (
            <TabLink id={key} key={key} to={{search: `?tab=${key}`}} title={name} />
          ))}
        </Tabs>
      </Box>
      <RightInfoPanelContent>
        <ErrorBoundary region="tab" resetErrorOnChange={[activeTab, explorerPath]}>
          {tabDefinitions.find((t) => t.key === activeTab)?.content()}
        </ErrorBoundary>
      </RightInfoPanelContent>
    </>
  );
};
