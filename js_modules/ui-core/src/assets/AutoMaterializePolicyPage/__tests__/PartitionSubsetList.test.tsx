import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {render, waitFor} from '@testing-library/react';

import {PartitionSubsetList} from '../PartitionSubsetList';
import {PARTITION_SUBSET_LIST_QUERY} from '../PartitionSubsetListQuery';

const RESULT_DATA = {
  data: {
    __typename: 'Query',
    truePartitionsForAutomationConditionEvaluationNode: ['p1', 'p2'],
  },
};

describe('PartitionSubsetList', () => {
  it('queries by assetJobKey when a jobName is provided', async () => {
    const resultFn = jest.fn(() => RESULT_DATA);
    const mocks: MockedResponse[] = [
      {
        request: {
          query: PARTITION_SUBSET_LIST_QUERY,
          variables: {
            assetKey: null,
            assetJobKey: {jobName: 'demo_job'},
            evaluationId: '7',
            nodeUniqueId: 'root',
          },
        },
        result: resultFn,
      },
    ];

    render(
      <MockedProvider mocks={mocks}>
        <PartitionSubsetList
          description="Requested partitions"
          assetKeyPath={null}
          jobName="demo_job"
          evaluationId="7"
          nodeUniqueId="root"
        />
      </MockedProvider>,
    );

    // MockedProvider only serves a response when the variables match exactly, so a
    // consumed mock proves the assetJobKey variable shape.
    await waitFor(() => expect(resultFn).toHaveBeenCalled());
  });

  it('queries by assetKey when no jobName is provided', async () => {
    const resultFn = jest.fn(() => RESULT_DATA);
    const mocks: MockedResponse[] = [
      {
        request: {
          query: PARTITION_SUBSET_LIST_QUERY,
          variables: {
            assetKey: {path: ['foo', 'bar']},
            assetJobKey: null,
            evaluationId: '7',
            nodeUniqueId: 'root',
          },
        },
        result: resultFn,
      },
    ];

    render(
      <MockedProvider mocks={mocks}>
        <PartitionSubsetList
          description="Requested partitions"
          assetKeyPath={['foo', 'bar']}
          evaluationId="7"
          nodeUniqueId="root"
        />
      </MockedProvider>,
    );

    await waitFor(() => expect(resultFn).toHaveBeenCalled());
  });
});
