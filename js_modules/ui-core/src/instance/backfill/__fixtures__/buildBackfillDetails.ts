import {MockedResponse} from '@apollo/client/testing';

import {buildPartitionBackfill} from '../../../graphql/builders';
// eslint-disable-next-line no-restricted-imports
import {PartitionBackfill} from '../../../graphql/types-do-not-use';
import {BackfillDetailsQuery} from '../types/useBackfillDetailsQuery.types';
import {BACKFILL_DETAILS_QUERY} from '../useBackfillDetailsQuery';

export function buildBackfillDetailsQuery(
  backfillId: string,
  partitionBackfill: Partial<PartitionBackfill>,
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
