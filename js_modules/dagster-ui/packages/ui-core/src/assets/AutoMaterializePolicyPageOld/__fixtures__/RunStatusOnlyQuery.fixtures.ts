import {MockedResponse} from '@apollo/client/testing';

import {RunStatus, buildRun} from '../../../graphql/types';
import {RUN_STATUS_ONLY} from '../AutomaterializeRunTag';
import {
  OldRunStatusOnlyQuery,
  OldRunStatusOnlyQueryVariables,
} from '../types/AutomaterializeRunTag.types';

export const buildRunStatusOnlyQuery = (
  runId: string,
  status: RunStatus,
): MockedResponse<OldRunStatusOnlyQuery, OldRunStatusOnlyQueryVariables> => {
  return {
    request: {
      query: RUN_STATUS_ONLY,
      variables: {runId},
    },
    result: {
      data: {
        __typename: 'Query',
        runOrError: buildRun({
          id: runId,
          status,
        }),
      },
    },
  };
};
