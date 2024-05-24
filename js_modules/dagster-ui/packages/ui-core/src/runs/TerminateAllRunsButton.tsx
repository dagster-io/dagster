import {gql, useApolloClient} from '@apollo/client';
import {Button} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import {useState} from 'react';

import {queuedStatuses} from './RunStatuses';
import {TerminationDialog} from './TerminationDialog';
import {
  TerminateRunIdsQuery,
  TerminateRunIdsQueryVariables,
} from './types/TerminateAllRunsButton.types';
import {RunsFilter} from '../graphql/types';

export const TerminateAllRunsButton = ({
  refetch,
  filter,
  disabled,
}: {
  refetch: () => void;
  filter: RunsFilter;
  disabled: boolean;
}) => {
  const [terminating, setTerminating] = useState<{[runId: string]: boolean} | null>(null);
  const client = useApolloClient();

  const onTerminateAll = async () => {
    const queuedRunIds = await client.query<TerminateRunIdsQuery, TerminateRunIdsQueryVariables>({
      query: TERMINATE_RUN_IDS_QUERY,
      variables: {filter},
    });
    setTerminating(
      queuedRunIds.data.pipelineRunsOrError.__typename === 'Runs'
        ? Object.fromEntries(
            queuedRunIds.data.pipelineRunsOrError.results.map((run) => [run.id, run.canTerminate]),
          )
        : {},
    );
  };
  return (
    <>
      <TerminationDialog
        isOpen={terminating !== null}
        selectedRuns={terminating || {}}
        selectedRunsAllQueued={isEqual(filter, {statuses: Array.from(queuedStatuses)})}
        onClose={() => setTerminating(null)}
        onComplete={() => refetch()}
      />
      <Button intent="danger" outlined disabled={disabled} onClick={onTerminateAll}>
        Terminate all…
      </Button>
    </>
  );
};

const TERMINATE_RUN_IDS_QUERY = gql`
  query TerminateRunIdsQuery($filter: RunsFilter!) {
    pipelineRunsOrError(filter: $filter) {
      ... on Runs {
        results {
          id
          status
          canTerminate
        }
      }
    }
  }
`;
