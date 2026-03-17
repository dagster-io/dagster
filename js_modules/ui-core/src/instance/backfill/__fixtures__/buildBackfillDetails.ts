import {MockedResponse} from '@apollo/client/testing';

import {buildPartitionBackfill} from '../../../graphql/builders';
import {BackfillDetailsQuery} from '../types/useBackfillDetailsQuery.types';
import {BACKFILL_DETAILS_QUERY} from '../useBackfillDetailsQuery';

export function buildBackfillDetailsQuery(
  backfillId: string,
  partitionBackfill: Partial<ReturnType<typeof buildPartitionBackfill>>,
): MockedResponse<BackfillDetailsQuery> {
  return {
    request: {
      query: BACKFILL_DETAILS_QUERY,
      variables: {backfillId},
    },
    result: {
      data: {
        __typename: 'Query',
        partitionBackfillOrError: buildPartitionBackfill(partitionBackfill),
      },
    },
  };
}
