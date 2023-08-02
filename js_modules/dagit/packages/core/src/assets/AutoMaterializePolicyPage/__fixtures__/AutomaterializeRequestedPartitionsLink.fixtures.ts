import {MockedResponse} from '@apollo/client/testing';
import faker from 'faker';

import {RunStatus, buildPipelineTag, buildRun, buildRuns} from '../../../graphql/types';
import {DagsterTag} from '../../../runs/RunTag';
import {RUN_STATUS_AND_PARTITION_KEY} from '../AutomaterializeRequestedPartitionsLink';
import {
  RunStatusAndPartitionKeyQuery,
  RunStatusAndPartitionKeyQueryVariables,
} from '../types/AutomaterializeRequestedPartitionsLink.types';

const MOCKED_STATUSES = [
  RunStatus.CANCELED,
  RunStatus.FAILURE,
  RunStatus.STARTED,
  RunStatus.SUCCESS,
  RunStatus.QUEUED,
];

const pickStatus = () => {
  const random = faker.datatype.number(MOCKED_STATUSES.length - 1);
  return MOCKED_STATUSES[random]!;
};

export const buildRunStatusAndPartitionKeyQuery = (
  partitionKeys: string[],
  runIds: string[],
): MockedResponse<RunStatusAndPartitionKeyQuery, RunStatusAndPartitionKeyQueryVariables> => {
  return {
    request: {
      query: RUN_STATUS_AND_PARTITION_KEY,
      variables: {
        filter: {runIds},
      },
    },
    result: {
      data: {
        __typename: 'Query',
        runsOrError: buildRuns({
          results: runIds.map((runId, ii) => {
            return buildRun({
              id: runId,
              status: pickStatus(),
              tags: [buildPipelineTag({key: DagsterTag.Partition, value: partitionKeys[ii]!})],
            });
          }),
        }),
      },
    },
  };
};
