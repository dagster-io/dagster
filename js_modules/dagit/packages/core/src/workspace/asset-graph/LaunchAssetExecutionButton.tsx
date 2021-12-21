import React from 'react';

import {LaunchRootExecutionButton} from '../../launchpad/LaunchRootExecutionButton';
import {repoAddressToSelector} from '../repoAddressToSelector';
import {RepoAddress} from '../types';

export const LaunchAssetExecutionButton: React.FC<{
  repoAddress: RepoAddress;
  assets: {opName: string | null; jobName: string | null}[];
}> = ({repoAddress, assets}) => {
  const jobName = assets[0].jobName;
  if (!jobName || !assets.every((a) => a.jobName === jobName && a.opName)) {
    return <span />;
  }

  return (
    <LaunchRootExecutionButton
      pipelineName={jobName}
      disabled={false}
      title={'Refresh'}
      getVariables={() => ({
        executionParams: {
          mode: 'default',
          executionMetadata: {},
          runConfigData: {},
          selector: {
            ...repoAddressToSelector(repoAddress),
            pipelineName: jobName,
            solidSelection: assets.map((a) => a.opName!),
          },
        },
      })}
    />
  );
};
