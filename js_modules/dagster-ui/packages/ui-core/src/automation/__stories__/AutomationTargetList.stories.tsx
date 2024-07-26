import {MockedProvider} from '@apollo/client/testing';
import {Meta} from '@storybook/react';

import {CustomAlertProvider} from '../../app/CustomAlertProvider';
import {SensorType} from '../../graphql/types';
import {
  buildStartKansasSuccess,
  buildStartLouisianaError,
} from '../../sensors/__fixtures__/SensorState.fixtures';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {AutomationTargetList} from '../AutomationTargetList';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'AutomationTargetList',
  component: AutomationTargetList,
} as Meta;

export const AutomationTargetListWithError = () => {
  return (
    <>
      <CustomAlertProvider />
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
    </>
  );
};
