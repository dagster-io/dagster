import {useMutation} from '@apollo/client';
import React from 'react';

import {AppContext} from '../../app/AppContext';
import {showLaunchError} from '../../execute/showLaunchError';
import {LAUNCH_PIPELINE_EXECUTION_MUTATION, handleLaunchResult} from '../../runs/RunUtils';
import {LaunchPipelineExecution} from '../../runs/types/LaunchPipelineExecution';
import {repoAddressToSelector} from '../repoAddressToSelector';
import {RepoAddress} from '../types';

export const useLaunchSingleAssetJob = () => {
  const {basePath} = React.useContext(AppContext);
  const [launchPipelineExecution] = useMutation<LaunchPipelineExecution>(
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
  );

  return React.useCallback(
    async (repoAddress: RepoAddress, definition: {jobName: string | null; opName: string}) => {
      if (!definition.jobName) {
        return;
      }

      try {
        const result = await launchPipelineExecution({
          variables: {
            executionParams: {
              selector: {
                pipelineName: definition.jobName,
                ...repoAddressToSelector(repoAddress),
              },
              mode: 'default',
              stepKeys: [definition.opName],
            },
          },
        });
        handleLaunchResult(basePath, definition.jobName, result, true);
      } catch (error) {
        showLaunchError(error as Error);
      }
    },
    [basePath, launchPipelineExecution],
  );
};
