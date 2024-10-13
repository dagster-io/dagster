import {MockedProvider} from '@apollo/client/testing';
import {Meta} from '@storybook/react';
import {RecoilRoot} from 'recoil';

import {CustomAlertProvider} from '../../app/CustomAlertProvider';
import {
  SensorType,
  buildAsset,
  buildAssetConnection,
  buildAssetKey,
  buildAssetSelection,
  buildPythonError,
} from '../../graphql/types';
import {
  buildStartKansasSuccess,
  buildStartLouisianaError,
} from '../../sensors/__fixtures__/SensorState.fixtures';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {AutomationTargetList} from '../AutomationTargetList';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'AutomationTargetList',
  component: AutomationTargetList,
} as Meta;

export const SingleJob = () => {
  return (
    <RecoilRoot>
      <MockedProvider mocks={[buildStartKansasSuccess(1000), buildStartLouisianaError(1000)]}>
        <WorkspaceProvider>
          <AutomationTargetList
            automationType={SensorType.ASSET}
            targets={[{pipelineName: 'pipelineName'}]}
            repoAddress={buildRepoAddress('a', 'b')}
            assetSelection={null}
          />
        </WorkspaceProvider>
      </MockedProvider>
    </RecoilRoot>
  );
};

export const MultipleJobs = () => {
  return (
    <RecoilRoot>
      <MockedProvider mocks={[buildStartKansasSuccess(1000), buildStartLouisianaError(1000)]}>
        <WorkspaceProvider>
          <AutomationTargetList
            automationType={SensorType.ASSET}
            targets={[{pipelineName: 'foo'}, {pipelineName: 'bar'}, {pipelineName: 'baz'}]}
            repoAddress={buildRepoAddress('a', 'b')}
            assetSelection={null}
          />
        </WorkspaceProvider>
      </MockedProvider>
    </RecoilRoot>
  );
};

export const AssetSelection = () => {
  const assetSelection = buildAssetSelection({
    assetSelectionString: 'asset_one',
    assetsOrError: buildAssetConnection({
      nodes: [buildAsset({id: 'asset_one', key: buildAssetKey({path: ['a', 'b']})})],
    }),
  });

  return (
    <RecoilRoot>
      <MockedProvider mocks={[buildStartKansasSuccess(1000), buildStartLouisianaError(1000)]}>
        <WorkspaceProvider>
          <AutomationTargetList
            automationType={SensorType.ASSET}
            targets={null}
            repoAddress={buildRepoAddress('a', 'b')}
            assetSelection={assetSelection}
          />
        </WorkspaceProvider>
      </MockedProvider>
    </RecoilRoot>
  );
};

export const MultipleAssetSelection = () => {
  const assetSelection = buildAssetSelection({
    assetSelectionString: 'asset_one and asset_two',
    assetsOrError: buildAssetConnection({
      nodes: [
        buildAsset({id: 'asset_one', key: buildAssetKey({path: ['a', 'b']})}),
        buildAsset({id: 'asset_two', key: buildAssetKey({path: ['c', 'd']})}),
      ],
    }),
  });

  return (
    <RecoilRoot>
      <MockedProvider mocks={[buildStartKansasSuccess(1000), buildStartLouisianaError(1000)]}>
        <WorkspaceProvider>
          <AutomationTargetList
            automationType={SensorType.ASSET}
            targets={null}
            repoAddress={buildRepoAddress('a', 'b')}
            assetSelection={assetSelection}
          />
        </WorkspaceProvider>
      </MockedProvider>
    </RecoilRoot>
  );
};

export const PythonError = () => {
  const assetSelection = buildAssetSelection({
    assetSelectionString: 'asset_one and asset_two',
    assetsOrError: buildPythonError({
      message: 'oh nooo',
    }),
  });

  return (
    <>
      <CustomAlertProvider />
      <RecoilRoot>
        <MockedProvider mocks={[buildStartKansasSuccess(1000), buildStartLouisianaError(1000)]}>
          <WorkspaceProvider>
            <AutomationTargetList
              automationType={SensorType.ASSET}
              targets={null}
              repoAddress={buildRepoAddress('a', 'b')}
              assetSelection={assetSelection}
            />
          </WorkspaceProvider>
        </MockedProvider>
      </RecoilRoot>
    </>
  );
};
