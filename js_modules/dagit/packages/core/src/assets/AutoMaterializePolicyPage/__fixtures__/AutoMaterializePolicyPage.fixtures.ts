import {MockedResponse} from '@apollo/client/testing';
import {DocumentNode} from 'graphql';

import {
  AutoMaterializeDecisionType,
  AutoMaterializePolicyType,
  buildAssetNode,
  buildAutoMaterializeAssetEvaluationNeedsMigrationError,
  buildAutoMaterializeAssetEvaluationRecord,
  buildAutoMaterializeAssetEvaluationRecords,
  buildAutoMaterializePolicy,
  buildFreshnessPolicy,
  buildMissingAutoMaterializeCondition,
  buildPartitionKeys,
} from '../../../graphql/types';
import {GET_POLICY_INFO_QUERY} from '../AutomaterializeRightPanel';
import {GET_EVALUATIONS_QUERY} from '../GetEvaluationsQuery';
import {
  GetPolicyInfoQuery,
  GetPolicyInfoQueryVariables,
} from '../types/AutomaterializeRightPanel.types';
import {
  GetEvaluationsQuery,
  GetEvaluationsQueryVariables,
} from '../types/GetEvaluationsQuery.types';
import {PAGE_SIZE} from '../useEvaluationsQueryResult';

export function buildQueryMock<
  TQuery extends {__typename: 'Query'},
  TVariables extends Record<string, any>
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

export const buildGetPolicyInfoQuery = ({
  variables,
  data,
}: {
  variables: GetPolicyInfoQueryVariables;
  data: Omit<GetPolicyInfoQuery, '__typename'>;
}): MockedResponse<GetPolicyInfoQuery> => {
  return buildQueryMock({
    query: GET_POLICY_INFO_QUERY,
    variables,
    data,
  });
};

const ONE_MINUTE = 1000 * 60;

export const buildEvaluationRecordsWithPartitions = () => {
  const now = Date.now();
  return [
    buildAutoMaterializeAssetEvaluationRecord({
      id: 'g',
      evaluationId: 27,
      timestamp: (now - ONE_MINUTE * 6) / 1000,
      numRequested: 2,
      numSkipped: 2,
      numDiscarded: 2,
    }),
    buildAutoMaterializeAssetEvaluationRecord({
      id: 'f',
      evaluationId: 24,
      timestamp: (now - ONE_MINUTE * 5) / 1000,
      numRequested: 2,
      numSkipped: 2,
      numDiscarded: 0,
    }),
    buildAutoMaterializeAssetEvaluationRecord({
      id: 'e',
      evaluationId: 20,
      timestamp: (now - ONE_MINUTE * 4) / 1000,
      numRequested: 0,
      numSkipped: 2410,
      numDiscarded: 3560,
    }),
    buildAutoMaterializeAssetEvaluationRecord({
      id: 'd',
      evaluationId: 13,
      timestamp: (now - ONE_MINUTE * 3) / 1000,
      numRequested: 2,
      numSkipped: 0,
      numDiscarded: 2,
    }),
    buildAutoMaterializeAssetEvaluationRecord({
      id: 'c',
      timestamp: (now - ONE_MINUTE * 2) / 1000,
      evaluationId: 12,
      numRequested: 0,
      numSkipped: 0,
      numDiscarded: 2,
    }),
    buildAutoMaterializeAssetEvaluationRecord({
      id: 'b',
      evaluationId: 4,
      timestamp: (now - ONE_MINUTE) / 1000,
      numRequested: 0,
      numSkipped: 2,
      numDiscarded: 0,
    }),
    buildAutoMaterializeAssetEvaluationRecord({
      id: 'a',
      evaluationId: 0,
      timestamp: now / 1000,
      numRequested: 2,
      numSkipped: 0,
      numDiscarded: 0,
    }),
  ];
};

export const buildEvaluationRecordsWithoutPartitions = () => {
  const now = Date.now();
  return [
    buildAutoMaterializeAssetEvaluationRecord({
      id: 'g',
      evaluationId: 27,
      timestamp: (now - ONE_MINUTE * 6) / 1000,
      numRequested: 1,
      numSkipped: 0,
      numDiscarded: 0,
    }),
    buildAutoMaterializeAssetEvaluationRecord({
      id: 'f',
      evaluationId: 24,
      timestamp: (now - ONE_MINUTE * 5) / 1000,
      numRequested: 0,
      numSkipped: 1,
      numDiscarded: 0,
    }),
    buildAutoMaterializeAssetEvaluationRecord({
      id: 'e',
      evaluationId: 20,
      timestamp: (now - ONE_MINUTE * 4) / 1000,
      numRequested: 0,
      numSkipped: 0,
      numDiscarded: 1,
    }),
  ];
};

export const SINGLE_MATERIALIZE_RECORD_WITH_PARTITIONS = buildAutoMaterializeAssetEvaluationRecord({
  evaluationId: 0,
  runIds: ['abcdef12'],
  conditions: [
    buildMissingAutoMaterializeCondition({
      decisionType: AutoMaterializeDecisionType.MATERIALIZE,
      partitionKeysOrError: buildPartitionKeys({
        partitionKeys: ['foo'],
      }),
    }),
  ],
});

export const SINGLE_MATERIALIZE_RECORD_NO_PARTITIONS = buildAutoMaterializeAssetEvaluationRecord({
  evaluationId: 0,
  runIds: ['abcdef12'],
  conditions: [
    buildMissingAutoMaterializeCondition({
      decisionType: AutoMaterializeDecisionType.MATERIALIZE,
    }),
  ],
});

export const Evaluations = {
  None: (assetKeyPath: string[]) => {
    return buildGetEvaluationsQuery({
      variables: {
        assetKey: {
          path: assetKeyPath,
        },
        cursor: undefined,
        limit: PAGE_SIZE + 1,
      },
      data: {
        autoMaterializeAssetEvaluationsOrError: buildAutoMaterializeAssetEvaluationRecords({
          currentEvaluationId: 1000,
          records: [],
        }),
      },
    });
  },
  Errors: (assetKeyPath: string[], single?: boolean) => {
    return buildGetEvaluationsQuery({
      variables: {
        assetKey: {path: assetKeyPath},
        cursor: undefined,
        limit: (single ? 1 : PAGE_SIZE) + 1,
      },
      data: {
        autoMaterializeAssetEvaluationsOrError: buildAutoMaterializeAssetEvaluationNeedsMigrationError(
          {
            message: 'Test message',
          },
        ),
      },
    });
  },
  Single: (assetKeyPath?: string[]) => {
    return buildGetEvaluationsQuery({
      variables: {
        assetKey: {path: assetKeyPath || ['test']},
        cursor: undefined,
        limit: 2,
      },
      data: {
        autoMaterializeAssetEvaluationsOrError: buildAutoMaterializeAssetEvaluationRecords({
          currentEvaluationId: 1000,
          records: assetKeyPath ? [SINGLE_MATERIALIZE_RECORD_WITH_PARTITIONS] : [],
        }),
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
        autoMaterializeAssetEvaluationsOrError: buildAutoMaterializeAssetEvaluationRecords({
          records: buildEvaluationRecordsWithPartitions(),
        }),
      },
    });
  },
};

export const Policies = {
  YesAutomaterializeNoFreshnessPolicy: (
    assetKeyPath: string[],
    policyType: AutoMaterializePolicyType = AutoMaterializePolicyType.EAGER,
  ) => {
    return buildGetPolicyInfoQuery({
      variables: {
        assetKey: {path: assetKeyPath},
      },
      data: {
        assetNodeOrError: buildAssetNode({
          freshnessPolicy: null,
          autoMaterializePolicy: buildAutoMaterializePolicy({
            policyType,
          }),
        }),
      },
    });
  },
  YesAutomaterializeYesFreshnessPolicy: (
    assetKeyPath: string[],
    policyType: AutoMaterializePolicyType = AutoMaterializePolicyType.EAGER,
  ) => {
    return buildGetPolicyInfoQuery({
      variables: {
        assetKey: {path: assetKeyPath},
      },
      data: {
        assetNodeOrError: buildAssetNode({
          freshnessPolicy: buildFreshnessPolicy({}),
          autoMaterializePolicy: buildAutoMaterializePolicy({
            policyType,
          }),
        }),
      },
    });
  },
  NoAutomaterializeYesFreshnessPolicy: (assetKeyPath: string[]) => {
    return buildGetPolicyInfoQuery({
      variables: {
        assetKey: {path: assetKeyPath},
      },
      data: {
        assetNodeOrError: buildAssetNode({
          freshnessPolicy: buildFreshnessPolicy(),
          autoMaterializePolicy: null,
        }),
      },
    });
  },
  NoAutomaterializeNoFreshnessPolicy: (assetKeyPath: string[]) => {
    return buildGetPolicyInfoQuery({
      variables: {
        assetKey: {path: assetKeyPath},
      },
      data: {
        assetNodeOrError: buildAssetNode({
          freshnessPolicy: null,
          autoMaterializePolicy: null,
        }),
      },
    });
  },
};
