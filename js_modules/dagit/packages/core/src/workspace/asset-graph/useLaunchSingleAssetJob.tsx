import {useMutation} from '@apollo/client';
import React from 'react';
import {useHistory} from 'react-router';

import {showLaunchError} from '../../launchpad/showLaunchError';
import {LAUNCH_PIPELINE_EXECUTION_MUTATION, handleLaunchResult} from '../../runs/RunUtils';
import {LaunchPipelineExecution} from '../../runs/types/LaunchPipelineExecution';
import {repoAddressToSelector} from '../repoAddressToSelector';
import {RepoAddress} from '../types';

export const useLaunchSingleAssetJob = () => {
  const history = useHistory();
  const [launchPipelineExecution] = useMutation<LaunchPipelineExecution>(
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
  );

  return React.useCallback(
    async (repoAddress: RepoAddress, jobName: string | null, opName: string | null) => {
      if (!jobName || !opName) {
        return;
      }

      try {
        const result = await launchPipelineExecution({
          variables: {
            executionParams: {
              mode: 'default',
              selector: {pipelineName: jobName, ...repoAddressToSelector(repoAddress)},
              stepKeys: [opName],
            },
          },
        });
        handleLaunchResult(jobName, result, history, {behavior: 'toast'});
      } catch (error) {
        showLaunchError(error as Error);
      }
    },
    [history, launchPipelineExecution],
  );
};
