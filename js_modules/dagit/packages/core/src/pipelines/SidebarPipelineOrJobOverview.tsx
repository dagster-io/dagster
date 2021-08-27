import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {Loading} from '../ui/Loading';
import {usePipelineSelector} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {Description} from './Description';
import {NonIdealPipelineQueryResult} from './NonIdealPipelineQueryResult';
import {PipelineExplorerPath} from './PipelinePathUtils';
import {SidebarSection} from './SidebarComponents';
import {SidebarModeSection, SIDEBAR_MODE_INFO_FRAGMENT} from './SidebarModeSection';
import {
  JobOverviewSidebarQuery,
  JobOverviewSidebarQueryVariables,
} from './types/JobOverviewSidebarQuery';

export const SidebarPipelineOrJobOverview: React.FC<{
  repoAddress: RepoAddress;
  explorerPath: PipelineExplorerPath;
}> = (props) => {
  const {flagPipelineModeTuples} = useFeatureFlags();
  const pipelineSelector = usePipelineSelector(props.repoAddress, props.explorerPath.pipelineName);

  const queryResult = useQuery<JobOverviewSidebarQuery, JobOverviewSidebarQueryVariables>(
    JOB_OVERVIEW_SIDEBAR_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      partialRefetch: true,
      variables: {pipelineSelector: pipelineSelector},
    },
  );

  return (
    <Loading queryResult={queryResult}>
      {({pipelineSnapshotOrError}) => {
        if (pipelineSnapshotOrError.__typename !== 'PipelineSnapshot') {
          return <NonIdealPipelineQueryResult result={pipelineSnapshotOrError} />;
        }

        let modes = pipelineSnapshotOrError.modes;

        if (flagPipelineModeTuples) {
          modes = modes.filter((m) => m.name === props.explorerPath.pipelineMode);
        }

        return (
          <div>
            <SidebarSection title={'Description'}>
              <Description
                description={pipelineSnapshotOrError.description || 'No description provided'}
              />
            </SidebarSection>
            <SidebarSection title={'Resources'}>
              {modes.map((mode) => (
                <SidebarModeSection mode={mode} key={mode.name} />
              ))}
            </SidebarSection>
          </div>
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
