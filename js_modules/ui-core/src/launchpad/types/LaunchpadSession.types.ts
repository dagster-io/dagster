// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PreviewConfigQueryVariables = Types.Exact<{
  pipeline: Types.PipelineSelector;
  runConfigData: Types.Scalars['RunConfigData']['input'];
  mode: Types.Scalars['String']['input'];
}>;

export type PreviewConfigQuery = {
  __typename: 'Query';
  isPipelineConfigValid:
    | {__typename: 'InvalidSubsetError'; message: string}
    | {__typename: 'PipelineConfigValidationValid'}
    | {__typename: 'PipelineNotFoundError'; message: string}
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      }
    | {
        __typename: 'RunConfigValidationInvalid';
        errors: Array<
          | {
              __typename: 'FieldNotDefinedConfigError';
              reason: Types.EvaluationErrorReason;
              message: string;
              fieldName: string;
              stack: {
                __typename: 'EvaluationStack';
                entries: Array<
                  | {__typename: 'EvaluationStackListItemEntry'; listIndex: number}
                  | {__typename: 'EvaluationStackMapKeyEntry'; mapKey: any}
                  | {__typename: 'EvaluationStackMapValueEntry'; mapKey: any}
                  | {__typename: 'EvaluationStackPathEntry'; fieldName: string}
                >;
              };
            }
          | {
              __typename: 'FieldsNotDefinedConfigError';
              reason: Types.EvaluationErrorReason;
              message: string;
              fieldNames: Array<string>;
              stack: {
                __typename: 'EvaluationStack';
                entries: Array<
                  | {__typename: 'EvaluationStackListItemEntry'; listIndex: number}
                  | {__typename: 'EvaluationStackMapKeyEntry'; mapKey: any}
                  | {__typename: 'EvaluationStackMapValueEntry'; mapKey: any}
                  | {__typename: 'EvaluationStackPathEntry'; fieldName: string}
                >;
              };
            }
          | {
              __typename: 'MissingFieldConfigError';
              reason: Types.EvaluationErrorReason;
              message: string;
              stack: {
                __typename: 'EvaluationStack';
                entries: Array<
                  | {__typename: 'EvaluationStackListItemEntry'; listIndex: number}
                  | {__typename: 'EvaluationStackMapKeyEntry'; mapKey: any}
                  | {__typename: 'EvaluationStackMapValueEntry'; mapKey: any}
                  | {__typename: 'EvaluationStackPathEntry'; fieldName: string}
                >;
              };
              field: {__typename: 'ConfigTypeField'; name: string};
            }
          | {
              __typename: 'MissingFieldsConfigError';
              reason: Types.EvaluationErrorReason;
              message: string;
              stack: {
                __typename: 'EvaluationStack';
                entries: Array<
                  | {__typename: 'EvaluationStackListItemEntry'; listIndex: number}
                  | {__typename: 'EvaluationStackMapKeyEntry'; mapKey: any}
                  | {__typename: 'EvaluationStackMapValueEntry'; mapKey: any}
                  | {__typename: 'EvaluationStackPathEntry'; fieldName: string}
                >;
              };
              fields: Array<{__typename: 'ConfigTypeField'; name: string}>;
            }
          | {
              __typename: 'RuntimeMismatchConfigError';
              reason: Types.EvaluationErrorReason;
              message: string;
              stack: {
                __typename: 'EvaluationStack';
                entries: Array<
                  | {__typename: 'EvaluationStackListItemEntry'; listIndex: number}
                  | {__typename: 'EvaluationStackMapKeyEntry'; mapKey: any}
                  | {__typename: 'EvaluationStackMapValueEntry'; mapKey: any}
                  | {__typename: 'EvaluationStackPathEntry'; fieldName: string}
                >;
              };
            }
          | {
              __typename: 'SelectorTypeConfigError';
              reason: Types.EvaluationErrorReason;
              message: string;
              stack: {
                __typename: 'EvaluationStack';
                entries: Array<
                  | {__typename: 'EvaluationStackListItemEntry'; listIndex: number}
                  | {__typename: 'EvaluationStackMapKeyEntry'; mapKey: any}
                  | {__typename: 'EvaluationStackMapValueEntry'; mapKey: any}
                  | {__typename: 'EvaluationStackPathEntry'; fieldName: string}
                >;
              };
            }
        >;
      };
};

export const PreviewConfigQueryVersion = 'd6d9fe33524d42b5159e04c018897ec90d991ebe6c2b46e5e5d736fc30f49c77';
