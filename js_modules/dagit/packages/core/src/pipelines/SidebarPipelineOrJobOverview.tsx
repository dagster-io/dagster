import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {Box} from '../ui/Box';
import {Loading} from '../ui/Loading';
import {isThisThingAJob, buildPipelineSelector, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {Description} from './Description';
import {NonIdealPipelineQueryResult} from './NonIdealPipelineQueryResult';
import {ExplorerPath} from './PipelinePathUtils';
import {SidebarSection} from './SidebarComponents';
import {SidebarModeSection, SIDEBAR_MODE_INFO_FRAGMENT} from './SidebarModeSection';
import {
  JobOverviewSidebarQuery,
  JobOverviewSidebarQueryVariables,
} from './types/JobOverviewSidebarQuery';

export const SidebarPipelineOrJobOverview: React.FC<{
  repoAddress: RepoAddress;
  explorerPath: ExplorerPath;
}> = (props) => {
  const {explorerPath, repoAddress} = props;
  const {pipelineName} = explorerPath;
  const pipelineSelector = buildPipelineSelector(repoAddress, pipelineName);

  const queryResult = useQuery<JobOverviewSidebarQuery, JobOverviewSidebarQueryVariables>(
    JOB_OVERVIEW_SIDEBAR_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      partialRefetch: true,
      variables: {pipelineSelector: pipelineSelector},
    },
  );

  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineName);

  return (
    <Loading queryResult={queryResult}>
      {({pipelineSnapshotOrError}) => {
        if (pipelineSnapshotOrError.__typename !== 'PipelineSnapshot') {
          return <NonIdealPipelineQueryResult isGraph={isJob} result={pipelineSnapshotOrError} />;
        }

        const modes = pipelineSnapshotOrError.modes;

        return (
          <>
            <SidebarSection title={'Description'}>
              <Box padding={{vertical: 16, horizontal: 24}}>
                <Description
                  description={pipelineSnapshotOrError.description || 'No description provided'}
                />
              </Box>
            </SidebarSection>
            <SidebarSection title={'Resources'}>
              <Box padding={{vertical: 16, horizontal: 24}}>
                {modes.map((mode) => (
                  <SidebarModeSection mode={mode} key={mode.name} />
                ))}
              </Box>
            </SidebarSection>
          </>
        );
      }}
    </Loading>
  );
};

const JOB_OVERVIEW_SIDEBAR_QUERY = gql`
  query JobOverviewSidebarQuery($pipelineSelector: PipelineSelector!) {
    pipelineSnapshotOrError(activePipelineSelector: $pipelineSelector) {
      ... on PipelineSnapshot {
        id
        name
        description
        modes {
          id
          ...SidebarModeInfoFragment
        }
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on PipelineSnapshotNotFoundError {
        message
      }
      ... on PythonError {
        message
      }
    }
  }
  ${SIDEBAR_MODE_INFO_FRAGMENT}
`;
