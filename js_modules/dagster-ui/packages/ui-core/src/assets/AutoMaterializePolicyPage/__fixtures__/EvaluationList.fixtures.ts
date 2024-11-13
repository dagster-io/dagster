import faker from 'faker';

import {
  buildAssetConditionEvaluation,
  buildAssetConditionEvaluationRecord,
  buildAutomationConditionEvaluationNode,
} from '../../../graphql/types';

const ONE_MINUTE = 60 * 1000;

export const buildEvaluationRecordsForList = (length: number) => {
  const now = Date.now();
  const evaluationId = 100;
  return new Array(length).fill(null).map((_, ii) => {
    const evaluationNodes = new Array(30).fill(null).map((_, jj) => {
      const id = faker.lorem.word();
      return buildAutomationConditionEvaluationNode({
        startTimestamp: 0 + jj,
        endTimestamp: 10 + jj,
        uniqueId: id,
        userLabel: faker.lorem.word(),
        isPartitioned: false,
        numTrue: 0,
      });
    });

    return buildAssetConditionEvaluationRecord({
      id: `evaluation-${ii}`,
      evaluationId: `${evaluationId + ii}`,
      evaluation: buildAssetConditionEvaluation({
        rootUniqueId: 'my-root',
      }),
      timestamp: (now - ONE_MINUTE * ii) / 1000,
      numRequested: Math.random() > 0.5 ? 1 : 0,
      runIds: Array.from({length: Math.floor(Math.random() * 5)}).map(() =>
        faker.datatype.uuid().slice(0, 8),
      ),
      isLegacy: false,
      rootUniqueId: 'my-root',
      evaluationNodes: [
        buildAutomationConditionEvaluationNode({
          startTimestamp: 0,
          endTimestamp: 1000,
          uniqueId: 'my-root',
          userLabel: faker.lorem.word(),
          isPartitioned: false,
          numTrue: 0,
          childUniqueIds: evaluationNodes.map((node) => node.uniqueId),
        }),
        ...evaluationNodes,
      ],
    });
  });
};
