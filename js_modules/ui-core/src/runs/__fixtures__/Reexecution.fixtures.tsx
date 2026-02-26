import {MockedResponse} from '@apollo/client/testing';

import {ReexecutionParams} from '../../graphql/types';
import {LAUNCH_PIPELINE_REEXECUTION_MUTATION} from '../RunUtils';
import {LaunchPipelineReexecutionMutation} from '../types/RunUtils.types';

export const buildLaunchPipelineReexecutionSuccessMock = (
  overrides: Pick<ReexecutionParams, 'parentRunId'> & Partial<ReexecutionParams>,
): MockedResponse<LaunchPipelineReexecutionMutation> => ({
  request: {
    query: LAUNCH_PIPELINE_REEXECUTION_MUTATION,
    variables: {reexecutionParams: {strategy: 'FROM_FAILURE', ...overrides}},
  },
  result: {
    data: {
      __typename: 'Mutation',
      launchPipelineReexecution: {
        __typename: 'LaunchRunSuccess',
        run: {
          id: '1234',
          pipelineName: '1234',
          rootRunId: null,
          parentRunId: overrides.parentRunId,
          __typename: 'Run',
        },
      },
    },
  },
});

export const buildLaunchPipelineReexecutionErrorMock = (
  overrides: Pick<ReexecutionParams, 'parentRunId'> & Partial<ReexecutionParams>,
): MockedResponse<LaunchPipelineReexecutionMutation> => ({
  request: {
    query: LAUNCH_PIPELINE_REEXECUTION_MUTATION,
    variables: {reexecutionParams: {strategy: 'FROM_FAILURE', ...overrides}},
  },
  result: {
    data: {
      __typename: 'Mutation',
      launchPipelineReexecution: {
        __typename: 'PythonError',
        errorChain: [],
        message: 'A wild python error appeared!',
        stack: [],
      },
    },
  },
});
