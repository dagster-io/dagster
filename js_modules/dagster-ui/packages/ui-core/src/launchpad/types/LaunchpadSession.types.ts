// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PreviewConfigQueryVariables = Types.Exact<{
  pipeline: Types.PipelineSelector;
  runConfigData: Types.Scalars['RunConfigData'];
  mode: Types.Scalars['String'];
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

export type PipelineExecutionConfigSchemaQueryVariables = Types.Exact<{
  selector: Types.PipelineSelector;
  mode?: Types.InputMaybe<Types.Scalars['String']>;
}>;

export type PipelineExecutionConfigSchemaQuery = {
  __typename: 'Query';
  runConfigSchemaOrError:
    | {__typename: 'InvalidSubsetError'}
    | {__typename: 'ModeNotFoundError'; message: string}
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PythonError'}
    | {
        __typename: 'RunConfigSchema';
        rootDefaultYaml: string;
        rootConfigType:
          | {__typename: 'ArrayConfigType'; key: string}
          | {__typename: 'CompositeConfigType'; key: string}
          | {__typename: 'EnumConfigType'; key: string}
          | {__typename: 'MapConfigType'; key: string}
          | {__typename: 'NullableConfigType'; key: string}
          | {__typename: 'RegularConfigType'; key: string}
          | {__typename: 'ScalarUnionConfigType'; key: string};
        allConfigTypes: Array<
          | {
              __typename: 'ArrayConfigType';
              key: string;
              description: string | null;
              isSelector: boolean;
              typeParamKeys: Array<string>;
            }
          | {
              __typename: 'CompositeConfigType';
              key: string;
              description: string | null;
              isSelector: boolean;
              typeParamKeys: Array<string>;
              fields: Array<{
                __typename: 'ConfigTypeField';
                name: string;
                description: string | null;
                isRequired: boolean;
                configTypeKey: string;
                defaultValueAsJson: string | null;
              }>;
            }
          | {
              __typename: 'EnumConfigType';
              givenName: string;
              key: string;
              description: string | null;
              isSelector: boolean;
              typeParamKeys: Array<string>;
              values: Array<{
                __typename: 'EnumConfigValue';
                value: string;
                description: string | null;
              }>;
            }
          | {
              __typename: 'MapConfigType';
              keyLabelName: string | null;
              key: string;
              description: string | null;
              isSelector: boolean;
              typeParamKeys: Array<string>;
            }
          | {
              __typename: 'NullableConfigType';
              key: string;
              description: string | null;
              isSelector: boolean;
              typeParamKeys: Array<string>;
            }
          | {
              __typename: 'RegularConfigType';
              givenName: string;
              key: string;
              description: string | null;
              isSelector: boolean;
              typeParamKeys: Array<string>;
            }
          | {
              __typename: 'ScalarUnionConfigType';
              key: string;
              scalarTypeKey: string;
              nonScalarTypeKey: string;
              description: string | null;
              isSelector: boolean;
              typeParamKeys: Array<string>;
            }
        >;
      };
};

export type LaunchpadSessionRunConfigSchemaFragment_InvalidSubsetError_ = {
  __typename: 'InvalidSubsetError';
};

export type LaunchpadSessionRunConfigSchemaFragment_ModeNotFoundError_ = {
  __typename: 'ModeNotFoundError';
  message: string;
};

export type LaunchpadSessionRunConfigSchemaFragment_PipelineNotFoundError_ = {
  __typename: 'PipelineNotFoundError';
};

export type LaunchpadSessionRunConfigSchemaFragment_PythonError_ = {__typename: 'PythonError'};

export type LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_ = {
  __typename: 'RunConfigSchema';
  rootDefaultYaml: string;
  rootConfigType:
    | {__typename: 'ArrayConfigType'; key: string}
    | {__typename: 'CompositeConfigType'; key: string}
    | {__typename: 'EnumConfigType'; key: string}
    | {__typename: 'MapConfigType'; key: string}
    | {__typename: 'NullableConfigType'; key: string}
    | {__typename: 'RegularConfigType'; key: string}
    | {__typename: 'ScalarUnionConfigType'; key: string};
  allConfigTypes: Array<
    | {
        __typename: 'ArrayConfigType';
        key: string;
        description: string | null;
        isSelector: boolean;
        typeParamKeys: Array<string>;
      }
    | {
        __typename: 'CompositeConfigType';
        key: string;
        description: string | null;
        isSelector: boolean;
        typeParamKeys: Array<string>;
        fields: Array<{
          __typename: 'ConfigTypeField';
          name: string;
          description: string | null;
          isRequired: boolean;
          configTypeKey: string;
          defaultValueAsJson: string | null;
        }>;
      }
    | {
        __typename: 'EnumConfigType';
        givenName: string;
        key: string;
        description: string | null;
        isSelector: boolean;
        typeParamKeys: Array<string>;
        values: Array<{__typename: 'EnumConfigValue'; value: string; description: string | null}>;
      }
    | {
        __typename: 'MapConfigType';
        keyLabelName: string | null;
        key: string;
        description: string | null;
        isSelector: boolean;
        typeParamKeys: Array<string>;
      }
    | {
        __typename: 'NullableConfigType';
        key: string;
        description: string | null;
        isSelector: boolean;
        typeParamKeys: Array<string>;
      }
    | {
        __typename: 'RegularConfigType';
        givenName: string;
        key: string;
        description: string | null;
        isSelector: boolean;
        typeParamKeys: Array<string>;
      }
    | {
        __typename: 'ScalarUnionConfigType';
        key: string;
        scalarTypeKey: string;
        nonScalarTypeKey: string;
        description: string | null;
        isSelector: boolean;
        typeParamKeys: Array<string>;
      }
  >;
};

export type LaunchpadSessionRunConfigSchemaFragment =
  | LaunchpadSessionRunConfigSchemaFragment_InvalidSubsetError_
  | LaunchpadSessionRunConfigSchemaFragment_ModeNotFoundError_
  | LaunchpadSessionRunConfigSchemaFragment_PipelineNotFoundError_
  | LaunchpadSessionRunConfigSchemaFragment_PythonError_
  | LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema_;

export type LaunchpadSessionModeNotFoundFragment = {
  __typename: 'ModeNotFoundError';
  message: string;
};
