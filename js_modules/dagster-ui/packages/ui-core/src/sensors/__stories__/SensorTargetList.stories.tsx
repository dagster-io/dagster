import {MockedProvider} from '@apollo/client/testing';
import {Meta} from '@storybook/react';

import {CustomAlertProvider} from '../../app/CustomAlertProvider';
import {SensorType, buildAssetSelection, buildPythonError, buildSensor} from '../../graphql/types';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {SensorTargetList} from '../SensorTargetList';
import {
  buildStartKansasSuccess,
  buildStartLouisianaError,
} from '../__fixtures__/SensorState.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'SensorTargetList',
  component: SensorTargetList,
} as Meta;

export const SensorTargetListWithError = () => {
  return (
    <>
      <CustomAlertProvider />
      <MockedProvider mocks={[buildStartKansasSuccess(1000), buildStartLouisianaError(1000)]}>
        <WorkspaceProvider>
          <SensorTargetList
            sensorType={SensorType.ASSET}
            targets={[{pipelineName: 'pipelineName'}]}
            repoAddress={buildRepoAddress('a', 'b')}
            selectionQueryResult={
              {
                data: {
                  __typename: 'Query',
                  sensorOrError: buildSensor({
                    assetSelection: buildAssetSelection({
                      assetsOrError: buildPythonError(),
                    }),
                  }),
                },
              } as any
            }
          />
        </WorkspaceProvider>
      </MockedProvider>
    </>
  );
};
