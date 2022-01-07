import {useMutation} from '@apollo/client';
import React from 'react';

import {AppContext} from '../../app/AppContext';
import {showLaunchError} from '../../launchpad/showLaunchError';
import {LAUNCH_PIPELINE_EXECUTION_MUTATION, handleLaunchResult} from '../../runs/RunUtils';
import {LaunchPipelineExecution} from '../../runs/types/LaunchPipelineExecution';
import {repoAddressToSelector} from '../repoAddressToSelector';
import {RepoAddress} from '../types';
import {AssetNodeFragment_assetKey} from './types/AssetNodeFragment';

export const useLaunchSingleAssetJob = () => {
  const {basePath} = React.useContext(AppContext);
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
              executionMetadata: {
                tags: [
                  {
                    key: "dagster/asset_key",
                    value: "TODO"
                  }
                ]

              }
            },
          },
        });
        handleLaunchResult(basePath, jobName, result, {
          openInTab: true,
        });
      } catch (error) {
        showLaunchError(error as Error);
      }
    },
    [basePath, launchPipelineExecution],
  );
};
