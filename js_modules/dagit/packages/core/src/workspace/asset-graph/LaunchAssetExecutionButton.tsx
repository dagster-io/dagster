import React from 'react';

import {LaunchRootExecutionButton} from '../../launchpad/LaunchRootExecutionButton';
import {RepoAddress} from '../types';

export const LaunchAssetExecutionButton: React.FC<{
  repoAddress: RepoAddress;
  assetJobName: string;
  assets: {opName: string | null}[];
}> = ({repoAddress, assets, assetJobName}) => {
  if (!assets.every((a) => a.opName)) {
    return <span />;
  }
  return (
    <LaunchRootExecutionButton
      pipelineName={assetJobName}
      disabled={false}
      title={'Refresh'}
      getVariables={() => ({
        executionParams: {
          mode: 'default',
          executionMetadata: {},
          runConfigData: {},
          selector: {
            repositoryLocationName: repoAddress.location,
            repositoryName: repoAddress.name,
            pipelineName: assetJobName,
            solidSelection: assets.map((o) => o.opName!),
          },
        },
      })}
    />
  );
};
