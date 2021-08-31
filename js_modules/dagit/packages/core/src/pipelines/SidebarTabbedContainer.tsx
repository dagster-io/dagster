import {gql} from '@apollo/client';
import {Colors, Icon, IconName} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useFeatureFlags} from '../app/Flags';
import {SolidNameOrPath} from '../solids/SolidNameOrPath';
import {TypeExplorerContainer} from '../typeexplorer/TypeExplorerContainer';
import {TypeListContainer} from '../typeexplorer/TypeListContainer';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {PipelineExplorerJobContext} from './PipelineExplorerJobContext';
import {PipelineExplorerPath} from './PipelinePathUtils';
import {SidebarPipelineInfo, SIDEBAR_PIPELINE_INFO_FRAGMENT} from './SidebarPipelineInfo';
import {SidebarSolidContainer} from './SidebarSolidContainer';
import {SidebarTabbedContainerPipelineFragment} from './types/SidebarTabbedContainerPipelineFragment';

type TabKey = 'types' | 'info' | 'jobs';

interface TabDefinition {
  name: string;
  icon: IconName;
  key: TabKey;
  content: () => React.ReactNode;
}

interface ISidebarTabbedContainerProps {
  pageContext: 'graph' | 'job';
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
    pageContext,
  } = props;

  const {flagPipelineModeTuples} = useFeatureFlags();
  const jobContext = React.useContext(PipelineExplorerJobContext);

  const activeTab = tab || 'info';

  const TabDefinitions: TabDefinition[] = [
    {
      name: 'Info',
      icon: 'data-lineage',
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
      icon: 'manual',
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

  if (flagPipelineModeTuples) {
    TabDefinitions.push({
      name: 'Related jobs',
      icon: 'send-to-graph',
      key: 'jobs',
      content: () => (
        <JobsForGraphName repoAddress={repoAddress} job={pipeline} pageContext={pageContext} />
      ),
    });
  }

  return (
    <>
      <TabContainer>
        {TabDefinitions.map(({name, icon, key}) => (
          <Link to={{search: `?tab=${key}`}} key={key}>
            <Tab key={key} active={key === activeTab}>
              <Icon icon={icon} style={{marginRight: 8}} />
              {name}
            </Tab>
          </Link>
        ))}
      </TabContainer>
      {TabDefinitions.find((t) => t.key === activeTab)?.content()}
    </>
  );
};

const JobsForGraphName: React.FC<{
  job: SidebarTabbedContainerPipelineFragment;
  repoAddress?: RepoAddress;
  pageContext: 'graph' | 'job';
}> = React.memo(({job, repoAddress, pageContext}) => {
  const {allRepos} = React.useContext(WorkspaceContext);
  const {graphName} = job;
  const matches = allRepos.reduce((accum, repo) => {
    const {repository, repositoryLocation} = repo;
    const targetRepoAddress = buildRepoAddress(repository.name, repositoryLocation.name);
    const targetRepoString = repoAddressAsString(targetRepoAddress);
    const {pipelines} = repository;
    const matchingGraph = pipelines.filter((pipeline) => {
      return (
        pipeline.graphName === graphName &&
        repoAddress === targetRepoAddress &&
        // Don't include the job we're looking at.
        (pageContext === 'graph' || pipeline.name !== job.name)
      );
    });

    if (!matchingGraph.length) {
      return accum;
    }

    return [
      ...accum,
      ...matchingGraph.map((match) => (
        <Group direction="column" spacing={2} key={match.name}>
          <Link
            key={match.name}
            to={workspacePathFromAddress(targetRepoAddress, `/jobs/${match.name}`)}
            style={{wordBreak: 'break-word'}}
          >
            <strong>{match.name}</strong>
          </Link>
          <Link
            style={{color: Colors.GRAY3, fontSize: '12px', wordBreak: 'break-word'}}
            to={workspacePathFromAddress(targetRepoAddress)}
          >
            {targetRepoString}
          </Link>
        </Group>
      )),
    ];
  }, [] as React.ReactNode[]);

  return (
    <Box padding={16}>
      {matches.length ? (
        <Group direction="column" spacing={16}>
          <Box padding={{bottom: 2}}>
            {pageContext === 'graph'
              ? 'The following jobs use this graph:'
              : 'The following jobs also use this graph:'}
          </Box>
          {matches}
        </Group>
      ) : (
        <div>There are no other jobs using this graph.</div>
      )}
    </Box>
  );
});

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
`;
