import {MockedResponse} from '@apollo/client/testing';

import {RUNNING_BACKFILLS_NOTICE_QUERY} from '../RunningBackfillsNotice';
import {RunningBackfillsNoticeQuery} from '../types/RunningBackfillsNotice.types';

export const NoRunningBackfills: MockedResponse<RunningBackfillsNoticeQuery> = {
  request: {
    query: RUNNING_BACKFILLS_NOTICE_QUERY,
    variables: {},
  },
  result: {
    data: {
      __typename: 'Query',
      partitionBackfillsOrError: {
        __typename: 'PartitionBackfills',
        results: [],
      },
    },
  },
};
