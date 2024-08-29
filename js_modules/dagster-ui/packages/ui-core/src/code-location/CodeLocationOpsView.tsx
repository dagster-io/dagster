import {Box, NonIdealState, SpinnerWithText} from '@dagster-io/ui-components';
import {useParams} from 'react-router-dom';

import {useQuery} from '../apollo-client';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {OPS_ROOT_QUERY, OpsRootWithData} from '../ops/OpsRoot';
import {OpsRootQuery, OpsRootQueryVariables} from '../ops/types/OpsRoot.types';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
}

export const CodeLocationOpsView = ({repoAddress}: Props) => {
  const {name} = useParams<{name?: string}>();
  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<OpsRootQuery, OpsRootQueryVariables>(OPS_ROOT_QUERY, {
    variables: {repositorySelector},
  });

  const {data, loading} = queryResult;

  const repoString = repoAddressAsHumanString(repoAddress);

  if (loading) {
    return (
      <Box padding={64} flex={{direction: 'row', justifyContent: 'center'}}>
        <SpinnerWithText label="Loading ops…" />
      </Box>
    );
  }

  if (!data || !data.repositoryOrError) {
    return (
      <Box padding={64}>
        <NonIdealState
          icon="op"
          title="An unexpected error occurred"
          description={`An error occurred while loading ops for ${repoString}`}
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

  const {repositoryOrError} = data;
  const {usedSolids} = repositoryOrError;

  if (!usedSolids.length) {
    return (
      <Box padding={64}>
        <NonIdealState
          icon="op"
          title="No ops found"
          description={`The repository ${repoAddressAsHumanString(
            repoAddress,
          )} does not contain any ops.`}
        />
      </Box>
    );
  }

  return <OpsRootWithData name={name} repoAddress={repoAddress} usedSolids={usedSolids} />;
};
