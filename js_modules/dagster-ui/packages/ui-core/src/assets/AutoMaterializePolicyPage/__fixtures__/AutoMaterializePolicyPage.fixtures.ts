import {MockedResponse} from '@apollo/client/testing';
import {DocumentNode} from 'graphql';

import {
  AutoMaterializeDecisionType,
  buildAssetConditionEvaluation,
  buildAssetConditionEvaluationRecord,
  buildAssetConditionEvaluationRecords,
  buildAssetKey,
  buildAssetNode,
  buildAutoMaterializeAssetEvaluationRecord,
  buildAutoMaterializePolicy,
  buildAutoMaterializeRule,
  buildAutoMaterializeRuleEvaluation,
  buildAutoMaterializeRuleWithRuleEvaluations,
  buildParentMaterializedRuleEvaluationData,
  buildPartitionKeys,
  buildUnpartitionedAssetConditionEvaluationNode,
} from '../../../graphql/types';
import {GET_EVALUATIONS_QUERY} from '../GetEvaluationsQuery';
import {
  GetEvaluationsQuery,
  GetEvaluationsQueryVariables,
} from '../types/GetEvaluationsQuery.types';
import {PAGE_SIZE} from '../useEvaluationsQueryResult';

export function buildQueryMock<
  TQuery extends {__typename: 'Query'},
  TVariables extends Record<string, any>,
>({
  query,
  variables,
  data,
}: {
  query: DocumentNode;
  variables: TVariables;
  data: Omit<TQuery, '__typename'>;
}): MockedResponse<TQuery> {
  return {
    request: {
      query,
      variables,
    },
    result: {
      data: {
        __typename: 'Query',
        ...data,
      } as TQuery,
    },
  };
}

export const buildGetEvaluationsQuery = ({
  variables,
  data,
}: {
  variables: GetEvaluationsQueryVariables;
  data: Omit<GetEvaluationsQuery, '__typename'>;
}): MockedResponse<GetEvaluationsQuery> => {
  return buildQueryMock({
    query: GET_EVALUATIONS_QUERY,
    variables,
    data,
  });
};

const ONE_MINUTE = 1000 * 60;

export const TEST_EVALUATION_ID = 27;

export const buildEvaluationRecordsWithPartitions = () => {
  const now = Date.now();
  return [
    buildAssetConditionEvaluationRecord({
      numRequested: 2,
      evaluation: buildAssetConditionEvaluation({
        rootUniqueId: '1',
        evaluationNodes: [
          buildUnpartitionedAssetConditionEvaluationNode({
            uniqueId: '1',
          }),
        ],
      }),
    }) as any,
    buildAssetConditionEvaluationRecord({
      id: 'f',
      evaluationId: 24,
      timestamp: (now - ONE_MINUTE * 5) / 1000,
      numRequested: 2,
    }),
    buildAssetConditionEvaluationRecord({
      id: 'e',
      evaluationId: 20,
      timestamp: (now - ONE_MINUTE * 4) / 1000,
      numRequested: 0,
    }),
    buildAssetConditionEvaluationRecord({
      id: 'd',
      evaluationId: 13,
      timestamp: (now - ONE_MINUTE * 3) / 1000,
      numRequested: 2,
    }),
    buildAssetConditionEvaluationRecord({
      id: 'c',
      timestamp: (now - ONE_MINUTE * 2) / 1000,
      evaluationId: 12,
      numRequested: 0,
    }),
    buildAssetConditionEvaluationRecord({
      id: 'b',
      evaluationId: 4,
      timestamp: (now - ONE_MINUTE) / 1000,
      numRequested: 0,
    }),
    buildAssetConditionEvaluationRecord({
      id: 'a',
      evaluationId: 0,
      timestamp: now / 1000,
      numRequested: 2,
    }),
  ];
};

export const buildEvaluationRecordsWithoutPartitions = () => {
  const now = Date.now();
  return [
    buildAssetConditionEvaluationRecord({
      id: 'g',
      evaluationId: TEST_EVALUATION_ID,
      timestamp: (now - ONE_MINUTE * 6) / 1000,
      numRequested: 1,
    }),
    buildAssetConditionEvaluationRecord({
      id: 'f',
      evaluationId: 24,
      timestamp: (now - ONE_MINUTE * 5) / 1000,
      numRequested: 0,
    }),
    buildAssetConditionEvaluationRecord({
      id: 'e',
      evaluationId: 20,
      timestamp: (now - ONE_MINUTE * 4) / 1000,
      numRequested: 0,
    }),
  ];
};

export const SINGLE_MATERIALIZE_RECORD_WITH_PARTITIONS = buildAutoMaterializeAssetEvaluationRecord({
  evaluationId: TEST_EVALUATION_ID,
  runIds: ['abcdef12'],
  rulesWithRuleEvaluations: [
    buildAutoMaterializeRuleWithRuleEvaluations({
      rule: buildAutoMaterializeRule({
        decisionType: AutoMaterializeDecisionType.MATERIALIZE,
        description: `Upstream data has changed since latest materialization`,
      }),
      ruleEvaluations: [
        buildAutoMaterializeRuleEvaluation({
          evaluationData: buildParentMaterializedRuleEvaluationData({
            updatedAssetKeys: [buildAssetKey({path: ['upstream_1']})],
          }),
          partitionKeysOrError: buildPartitionKeys({
            partitionKeys: ['bar'],
          }),
        }),
        buildAutoMaterializeRuleEvaluation({
          evaluationData: buildParentMaterializedRuleEvaluationData({
            updatedAssetKeys: [
              buildAssetKey({path: ['upstream_1']}),
              buildAssetKey({path: ['upstream_2']}),
            ],
          }),
          partitionKeysOrError: buildPartitionKeys({
            partitionKeys: ['foo'],
          }),
        }),
      ],
    }),
    buildAutoMaterializeRuleWithRuleEvaluations({
      rule: buildAutoMaterializeRule({
        decisionType: AutoMaterializeDecisionType.SKIP,
        description: `Waiting on upstream data`,
      }),
      ruleEvaluations: [
        buildAutoMaterializeRuleEvaluation({
          evaluationData: null,
          partitionKeysOrError: buildPartitionKeys({
            partitionKeys: ['gomez'],
          }),
        }),
      ],
    }),
  ],
});

export const SINGLE_MATERIALIZE_RECORD_NO_PARTITIONS = buildAutoMaterializeAssetEvaluationRecord({
  evaluationId: TEST_EVALUATION_ID,
  runIds: ['abcdef12'],
  rulesWithRuleEvaluations: [
    buildAutoMaterializeRuleWithRuleEvaluations({
      rule: buildAutoMaterializeRule({
        decisionType: AutoMaterializeDecisionType.MATERIALIZE,
        description: `Materialization is missing`,
      }),
      ruleEvaluations: [
        buildAutoMaterializeRuleEvaluation({
          evaluationData: null,
          partitionKeysOrError: null,
        }),
      ],
    }),
  ],
});

export const BASE_AUTOMATERIALIZE_RULES = [
  buildAutoMaterializeRule({
    decisionType: AutoMaterializeDecisionType.MATERIALIZE,
    description: `Materialization is missing`,
  }),
  buildAutoMaterializeRule({
    decisionType: AutoMaterializeDecisionType.MATERIALIZE,
    description: `Upstream data has changed since latest materialization`,
  }),
  buildAutoMaterializeRule({
    decisionType: AutoMaterializeDecisionType.MATERIALIZE,
    description: `Required to meet this or downstream asset's freshness policy`,
  }),
  buildAutoMaterializeRule({
    decisionType: AutoMaterializeDecisionType.SKIP,
    description: `Waiting on upstream data`,
  }),
];

export const DISCARD_RULE = buildAutoMaterializeRule({
  decisionType: AutoMaterializeDecisionType.DISCARD,
  description: `Exceeds 5 materializations per minute`,
});

export const Evaluations = {
  None: (assetKeyPath: string[], single?: boolean) => {
    return buildGetEvaluationsQuery({
      variables: {
        assetKey: {path: assetKeyPath},
        cursor: single ? '2' : undefined,
        limit: (single ? 1 : PAGE_SIZE) + 1,
      },
      data: {
        assetNodeOrError: buildAssetNode({
          autoMaterializePolicy: buildAutoMaterializePolicy({
            rules: BASE_AUTOMATERIALIZE_RULES,
          }),
          currentAutoMaterializeEvaluationId: 1000,
        }),
        assetConditionEvaluationRecordsOrError: buildAssetConditionEvaluationRecords(),
      },
    });
  },
  Errors: (assetKeyPath: string[], single?: boolean) => {
    return buildGetEvaluationsQuery({
      variables: {
        assetKey: {path: assetKeyPath},
        cursor: single ? '2' : undefined,
        limit: (single ? 1 : PAGE_SIZE) + 1,
      },
      data: {
        assetNodeOrError: buildAssetNode({
          autoMaterializePolicy: buildAutoMaterializePolicy({
            rules: BASE_AUTOMATERIALIZE_RULES,
          }),
        }),
        assetConditionEvaluationRecordsOrError: buildAssetConditionEvaluationRecords(),
      },
    });
  },
  Single: (assetKeyPath?: string[], cursor?: string) => {
    return buildGetEvaluationsQuery({
      variables: {
        assetKey: {path: assetKeyPath || ['test']},
        cursor,
        limit: 2,
      },
      data: {
        assetNodeOrError: buildAssetNode({
          autoMaterializePolicy: buildAutoMaterializePolicy({
            rules: [...BASE_AUTOMATERIALIZE_RULES, DISCARD_RULE],
          }),
        }),
        assetConditionEvaluationRecordsOrError: buildAssetConditionEvaluationRecords(),
      },
    });
  },
  SinglePartitioned: (assetKeyPath: string[], cursor?: string) => {
    return buildGetEvaluationsQuery({
      variables: {
        assetKey: {path: assetKeyPath},
        cursor,
        limit: 2,
      },
      data: {
        assetNodeOrError: buildAssetNode({
          autoMaterializePolicy: buildAutoMaterializePolicy({
            rules: [...BASE_AUTOMATERIALIZE_RULES, DISCARD_RULE],
          }),
        }),
        assetConditionEvaluationRecordsOrError: buildAssetConditionEvaluationRecords(),
      },
    });
  },
  Some: (assetKeyPath: string[]) => {
    return buildGetEvaluationsQuery({
      variables: {
        assetKey: {path: assetKeyPath},
        cursor: undefined,
        limit: PAGE_SIZE + 1,
      },
      data: {
        assetNodeOrError: buildAssetNode({
          autoMaterializePolicy: buildAutoMaterializePolicy({
            rules: [...BASE_AUTOMATERIALIZE_RULES, DISCARD_RULE],
          }),
        }),
        assetConditionEvaluationRecordsOrError: buildAssetConditionEvaluationRecords(),
      },
    });
  },
};
