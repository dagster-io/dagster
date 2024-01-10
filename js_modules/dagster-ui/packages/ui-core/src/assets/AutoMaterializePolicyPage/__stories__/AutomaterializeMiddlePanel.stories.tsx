import {MockedProvider} from '@apollo/client/testing';
import * as React from 'react';

import {
  buildAsset,
  buildAssetConditionEvaluation,
  buildAssetConditionEvaluationRecord,
  buildAssetNode,
  buildDimensionPartitionKeys,
  buildPartitionDefinition,
  buildPartitionedAssetConditionEvaluationNode,
  buildUnpartitionedAssetConditionEvaluationNode,
} from '../../../graphql/types';
import {
  AutomaterializeMiddlePanel,
  AutomaterializeMiddlePanelWithData,
} from '../AutomaterializeMiddlePanel';
import {Evaluations, TEST_EVALUATION_ID} from '../__fixtures__/AutoMaterializePolicyPage.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize/AutomaterializeMiddlePanelWithData',
  component: AutomaterializeMiddlePanelWithData,
};

const path = ['test'];

export const Empty = () => {
  return (
    <MockedProvider mocks={[Evaluations.Single(path)]}>
      <div style={{width: '800px'}}>
        <AutomaterializeMiddlePanel assetKey={{path}} selectedEvaluationId={undefined} />
      </div>
    </MockedProvider>
  );
};

export const WithoutPartitions = () => {
  return (
    <MockedProvider mocks={[Evaluations.Single(path, `${TEST_EVALUATION_ID + 1}`)]}>
      <div style={{width: '800px'}}>
        <AutomaterializeMiddlePanel
          assetKey={{path}}
          definition={
            buildAssetNode({
              partitionKeysByDimension: [
                buildDimensionPartitionKeys({
                  partitionKeys: ['testing', 'testing2'],
                }),
              ],
            }) as any
          }
          selectedEvaluation={
            buildAssetConditionEvaluationRecord({
              evaluation: buildAssetConditionEvaluation({
                rootUniqueId: '1',
                evaluationNodes: [
                  buildUnpartitionedAssetConditionEvaluationNode({
                    uniqueId: '1',
                  }),
                ],
              }),
            }) as any
          }
          selectedEvaluationId={TEST_EVALUATION_ID}
        />
      </div>
    </MockedProvider>
  );
};

export const WithPartitions = () => {
  return (
    <MockedProvider mocks={[Evaluations.SinglePartitioned(path, `${TEST_EVALUATION_ID + 1}`)]}>
      <div style={{width: '800px'}}>
        <AutomaterializeMiddlePanel
          assetKey={{path}}
          definition={
            buildAssetNode({
              partitionKeysByDimension: [
                buildDimensionPartitionKeys({
                  partitionKeys: ['testing', 'testing2'],
                }),
              ],
            }) as any
          }
          selectedEvaluation={
            buildAssetConditionEvaluationRecord({
              evaluation: buildAssetConditionEvaluation({
                rootUniqueId: '1',
                evaluationNodes: [
                  buildPartitionedAssetConditionEvaluationNode({
                    uniqueId: '1',
                  }),
                ],
              }),
            }) as any
          }
          selectedEvaluationId={TEST_EVALUATION_ID}
        />
      </div>
    </MockedProvider>
  );
};
