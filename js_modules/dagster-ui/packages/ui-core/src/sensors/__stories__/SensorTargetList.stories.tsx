import {MockedProvider} from '@apollo/client/testing';
import {Meta} from '@storybook/react';

import {SensorType, buildAssetSelection, buildPythonError, buildSensor} from '../../graphql/types';
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
    <MockedProvider mocks={[buildStartKansasSuccess(1000), buildStartLouisianaError(1000)]}>
      <SensorTargetList
        sensorType={SensorType.ASSET}
        targets={[{pipelineName: 'any'}]}
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
    </MockedProvider>
  );
};
