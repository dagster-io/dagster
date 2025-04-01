import {useCallback} from 'react';
import {useHistory} from 'react-router-dom';

import {showLaunchError} from './showLaunchError';
import {useMutation} from '../apollo-client';
import {TelemetryAction, useTelemetryAction} from '../app/Telemetry';
import {
  LAUNCH_MULTIPLE_RUNS_MUTATION,
  LaunchBehavior,
  handleLaunchMultipleResult,
} from '../runs/RunUtils';
import {
  LaunchMultipleRunsMutation,
  LaunchMultipleRunsMutationVariables,
} from '../runs/types/RunUtils.types';

export function useLaunchMultipleRunsWithTelemetry() {
  const [launchMultipleRuns] = useMutation<
    LaunchMultipleRunsMutation,
    LaunchMultipleRunsMutationVariables
  >(LAUNCH_MULTIPLE_RUNS_MUTATION);

  const logTelemetry = useTelemetryAction();
  const history = useHistory();

  return useCallback(
    async (variables: LaunchMultipleRunsMutationVariables, behavior: LaunchBehavior) => {
      try {
        const executionParamsList = Array.isArray(variables.executionParamsList)
          ? variables.executionParamsList
          : [variables.executionParamsList];

        const jobNames = executionParamsList.map(
          (params) => params.selector.jobName || params.selector.pipelineName,
        );

        if (
          jobNames.length !== executionParamsList.length ||
          jobNames.includes(undefined) ||
          jobNames.includes(null)
        ) {
          throw new Error(
            'Error: Invalid job names. Each RunRequest must specify a job name to launch all runs',
          );
        }

        const metadata: {[key: string]: string | string[] | null | undefined} = {
          jobNames: jobNames.filter((name): name is string => name !== undefined),
          opSelection: undefined,
        };

        const result = (await launchMultipleRuns({variables})).data?.launchMultipleRuns;
        if (result) {
          handleLaunchMultipleResult(result, history, {behavior});
          logTelemetry(
            TelemetryAction.LAUNCH_MULTIPLE_RUNS,
            metadata as {[key: string]: string | string[] | null | undefined},
          );
        }

        return result;
      } catch (error) {
        console.error('error', error);
        showLaunchError(error as Error);
      }
      return undefined;
    },
    [history, launchMultipleRuns, logTelemetry],
  );
}
