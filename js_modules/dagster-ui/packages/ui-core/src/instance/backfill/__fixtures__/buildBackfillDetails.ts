import {MockedResponse} from '@apollo/client/testing';

import {PartitionBackfill, buildPartitionBackfill} from '../../../graphql/types';
import {BACKFILL_DETAILS_QUERY} from '../BackfillPage';
import {BackfillStatusesByAssetQuery} from '../types/BackfillPage.types';

export function buildBackfillDetailsQuery(
  backfillId: string,
  partitionBackfill: Partial<PartitionBackfill>,
): MockedResponse<BackfillStatusesByAssetQuery> {
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
