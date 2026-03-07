import {Box, NonIdealState, SpinnerWithText} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {CodeLocationSearchableList, SearchableListRow} from './CodeLocationSearchableList';
import {useQuery} from '../apollo-client';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {WORSKPACE_GRAPHS_QUERY} from '../workspace/WorkspaceGraphsQuery';
import {extractGraphsForRepo} from '../workspace/extractGraphsForRepo';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';
import {
  WorkspaceGraphsQuery,
  WorkspaceGraphsQueryVariables,
} from '../workspace/types/WorkspaceGraphsQuery.types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface Props {
  repoAddress: RepoAddress;
}

export const CodeLocationGraphsList = (props: Props) => {
  const {repoAddress} = props;

  const selector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<WorkspaceGraphsQuery, WorkspaceGraphsQueryVariables>(
    WORSKPACE_GRAPHS_QUERY,
    {variables: {selector}},
  );

  const {data, loading} = queryResult;

  const graphs = useMemo(() => {
    const repo = data?.repositoryOrError;
    if (!repo || repo.__typename !== 'Repository') {
      return [];
    }

    return extractGraphsForRepo(repo);
  }, [data]);

  const repoString = repoAddressAsHumanString(repoAddress);

  if (loading) {
    return (
      <Box padding={64} flex={{direction: 'row', justifyContent: 'center'}}>
        <SpinnerWithText label="Loading graphs…" />
      </Box>
    );
  }

  if (!data || !data.repositoryOrError) {
    return (
      <Box padding={64}>
        <NonIdealState
          icon="graph"
          title="An unexpected error occurred"
          description={`An error occurred while loading graphs for ${repoString}`}
        />
      </Box>
    );
  }

  if (data.repositoryOrError.__typename === 'PythonError') {
    return (
      <Box padding={64}>
        <PythonErrorInfo error={data.repositoryOrError} />
      </Box>
    );
  }

  if (data.repositoryOrError.__typename === 'RepositoryNotFoundError') {
    return (
      <Box padding={64}>
        <NonIdealState
          icon="op"
          title="Repository not found"
          description={`The repository ${repoString} could not be found in this workspace.`}
        />
      </Box>
    );
  }

  if (!graphs.length) {
    return (
      <Box padding={64}>
        <NonIdealState
          icon="graph"
          title="No graphs found"
          description={`The repository ${repoString} does not contain any graphs.`}
        />
      </Box>
    );
  }

  return (
    <CodeLocationSearchableList
      items={graphs}
      placeholder="Search graphs by name…"
      nameFilter={(graph, value) => graph.name.toLowerCase().includes(value)}
      renderRow={(graph) => (
        <SearchableListRow
          iconName="graph"
          label={graph.name}
          path={workspacePathFromAddress(repoAddress, graph.path)}
        />
      )}
    />
  );
};
