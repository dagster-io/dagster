import {Box, ErrorBoundary, Tab, Tabs} from '@dagster-io/ui-components';
import {useJobSidebarAlertsTabConfig} from '@shared/pipelines/useJobSidebarAlertsTabConfig';

import {gql, useQuery} from '../apollo-client';
import {
  AssetGraphSidebarQuery,
  AssetGraphSidebarQueryVariables,
} from './types/AssetGraphJobSidebar.types';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PipelineSelector} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {RightInfoPanelContent} from '../pipelines/GraphExplorer';
import {NonIdealPipelineQueryResult} from '../pipelines/NonIdealPipelineQueryResult';
import {
  SIDEBAR_ROOT_CONTAINER_FRAGMENT,
  SidebarContainerOverview,
} from '../pipelines/SidebarContainerOverview';
import {TabDefinition} from '../pipelines/types';
import {Loading} from '../ui/Loading';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';

interface Props {
  pipelineSelector: PipelineSelector;
}

export const AssetGraphJobSidebar = ({pipelineSelector}: Props) => {
  const queryResult = useQuery<AssetGraphSidebarQuery, AssetGraphSidebarQueryVariables>(
    ASSET_GRAPH_JOB_SIDEBAR,
    {
      variables: {pipelineSelector},
    },
  );

  const {repositoryName, repositoryLocationName} = pipelineSelector;
  const repoAddress = buildRepoAddress(repositoryName, repositoryLocationName);

  return (
    <Loading queryResult={queryResult}>
      {({pipelineSnapshotOrError}) => {
        if (pipelineSnapshotOrError.__typename !== 'PipelineSnapshot') {
          return (
            <NonIdealPipelineQueryResult
              isGraph
              result={pipelineSnapshotOrError}
              repoAddress={repoAddress}
            />
          );
        }

        return (
          <AssetGraphJobSidebarContent
            pipelineSelector={pipelineSelector}
            pipelineSnapshot={pipelineSnapshotOrError}
            repoAddress={repoAddress}
          />
        );
      }}
    </Loading>
  );
};

export const AssetGraphJobSidebarContent = ({
  repoAddress,
  pipelineSelector,
  pipelineSnapshot,
}: Props & {
  repoAddress: RepoAddress;
  pipelineSnapshot: Extract<
    AssetGraphSidebarQuery['pipelineSnapshotOrError'],
    {__typename: 'PipelineSnapshot'}
  >;
}) => {
  const [activeTab, setActiveTab] = useQueryPersistedState({
    queryKey: 'tab',
    defaults: {tab: 'info'},
  });

  const tabDefinitions: TabDefinition[] = [
    {
      name: 'Info',
      key: 'info' as const,
      content: () => (
        <SidebarContainerOverview container={pipelineSnapshot} repoAddress={repoAddress} />
      ),
    },
    useJobSidebarAlertsTabConfig({repoAddress, jobName: pipelineSelector.pipelineName}),
  ].filter((tab) => tab !== null);

  return (
    <>
      <Box padding={{horizontal: 24}} border="bottom">
        <Tabs selectedTabId={activeTab}>
          {tabDefinitions.map(({name, key}) => (
            <Tab id={key} key={key} onClick={() => setActiveTab(key)} title={name} />
          ))}
        </Tabs>
      </Box>
      <RightInfoPanelContent>
        <ErrorBoundary region="tab" resetErrorOnChange={[activeTab, pipelineSelector.pipelineName]}>
          {tabDefinitions.find((t) => t.key === activeTab)?.content()}
        </ErrorBoundary>
      </RightInfoPanelContent>
    </>
  );
};

const ASSET_GRAPH_JOB_SIDEBAR = gql`
  query AssetGraphSidebarQuery($pipelineSelector: PipelineSelector!) {
    pipelineSnapshotOrError(activePipelineSelector: $pipelineSelector) {
      ... on PipelineSnapshot {
        id
        ...SidebarRootContainerFragment
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on PipelineSnapshotNotFoundError {
        message
      }
      ...PythonErrorFragment
    }
  }

  ${SIDEBAR_ROOT_CONTAINER_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
