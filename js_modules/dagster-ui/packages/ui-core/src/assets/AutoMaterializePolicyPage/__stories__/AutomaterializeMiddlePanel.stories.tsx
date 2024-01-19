import {MockedProvider} from '@apollo/client/testing';

import {RunStatus} from '../../../graphql/types';
import {
  AutomaterializeMiddlePanel,
  AutomaterializeMiddlePanelWithData,
} from '../AutomaterializeMiddlePanel';
import {Evaluations, TEST_EVALUATION_ID} from '../__fixtures__/AutoMaterializePolicyPage.fixtures';
import {buildRunStatusOnlyQuery} from '../__fixtures__/RunStatusOnlyQuery.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize/AutomaterializeMiddlePanelWithData',
  component: AutomaterializeMiddlePanelWithData,
};

const path = ['test'];

export const Empty = () => {
  return (
    <MockedProvider
      mocks={[Evaluations.Single(path), buildRunStatusOnlyQuery('abcdef12', RunStatus.STARTED)]}
    >
      <div style={{width: '800px'}}>
        <AutomaterializeMiddlePanel
          assetKey={{path}}
          assetHasDefinedPartitions={false}
          selectedEvaluationId={undefined}
        />
      </div>
    </MockedProvider>
  );
};

export const WithoutPartitions = () => {
  return (
    <MockedProvider
      mocks={[
        Evaluations.Single(path, `${TEST_EVALUATION_ID + 1}`),
        buildRunStatusOnlyQuery('abcdef12', RunStatus.STARTED),
      ]}
    >
      <div style={{width: '800px'}}>
        <AutomaterializeMiddlePanel
          assetKey={{path}}
          assetHasDefinedPartitions={false}
          selectedEvaluationId={TEST_EVALUATION_ID}
        />
      </div>
    </MockedProvider>
  );
};

export const WithPartitions = () => {
  return (
    <MockedProvider
      mocks={[
        Evaluations.SinglePartitioned(path, `${TEST_EVALUATION_ID + 1}`),
        buildRunStatusOnlyQuery('abcdef12', RunStatus.STARTED),
      ]}
    >
      <div style={{width: '800px'}}>
        <AutomaterializeMiddlePanel
          assetKey={{path}}
          assetHasDefinedPartitions={true}
          selectedEvaluationId={TEST_EVALUATION_ID}
        />
      </div>
    </MockedProvider>
  );
};
