import {MockedResponse} from '@apollo/client/testing';
import {DocumentNode} from 'graphql';

import {
  AutoMaterializePolicyType,
  buildAssetNode,
  buildAutoMaterializeAssetEvaluationNeedsMigrationError,
  buildAutoMaterializeAssetEvaluationRecord,
  buildAutoMaterializeAssetEvaluationRecords,
  buildAutoMaterializePolicy,
  buildFreshnessPolicy,
} from '../../../graphql/types';
import {
  GET_EVALUATIONS_QUERY,
  GET_POLICY_INFO_QUERY,
  PAGE_SIZE,
} from '../AssetAutomaterializePolicyPage';
import {
  GetEvaluationsQuery,
  GetEvaluationsQueryVariables,
  GetPolicyInfoQuery,
  GetPolicyInfoQueryVariables,
} from '../types/AssetAutomaterializePolicyPage.types';

export function buildQueryMock<
  TQuery extends {__typename: 'DagitQuery'},
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
        __typename: 'DagitQuery',
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
          records: assetKeyPath
            ? [
                buildAutoMaterializeAssetEvaluationRecord({
                  evaluationId: 0,
                }),
              ]
            : [],
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
          records: [
            buildAutoMaterializeAssetEvaluationRecord({
              evaluationId: 0,
            }),
            buildAutoMaterializeAssetEvaluationRecord({
              evaluationId: 1,
            }),
            {
              ...buildAutoMaterializeAssetEvaluationRecord(),
              evaluationId: 2,
              numRequested: 0,
              numSkipped: 5,
            },
            buildAutoMaterializeAssetEvaluationRecord({
              evaluationId: 3,
            }),
            buildAutoMaterializeAssetEvaluationRecord({
              evaluationId: 3,
            }),
          ],
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
