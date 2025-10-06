// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type LaunchpadRootQueryVariables = Types.Exact<{
  pipelineName: Types.Scalars['String']['input'];
  repositoryName: Types.Scalars['String']['input'];
  repositoryLocationName: Types.Scalars['String']['input'];
  assetSelection?: Types.InputMaybe<Array<Types.AssetKeyInput> | Types.AssetKeyInput>;
}>;

export type LaunchpadRootQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'; message: string}
    | {
        __typename: 'Pipeline';
        id: string;
        isJob: boolean;
        isAssetJob: boolean;
        name: string;
        modes: Array<{__typename: 'Mode'; id: string; name: string; description: string | null}>;
        presets: Array<{
          __typename: 'PipelinePreset';
          name: string;
          mode: string;
          solidSelection: Array<string> | null;
          runConfigYaml: string;
          tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
        }>;
        tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
      }
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
      };
  partitionSetsOrError:
    | {
        __typename: 'PartitionSets';
        results: Array<{
          __typename: 'PartitionSet';
          id: string;
          name: string;
          mode: string;
          solidSelection: Array<string> | null;
        }>;
      }
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
      };
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

export type LaunchpadSessionPartitionSetsFragment = {
  __typename: 'PartitionSets';
  results: Array<{
    __typename: 'PartitionSet';
    id: string;
    name: string;
    mode: string;
    solidSelection: Array<string> | null;
  }>;
};

export type LaunchpadSessionPipelineFragment = {
  __typename: 'Pipeline';
  id: string;
  isJob: boolean;
  isAssetJob: boolean;
  name: string;
  modes: Array<{__typename: 'Mode'; id: string; name: string; description: string | null}>;
  presets: Array<{
    __typename: 'PipelinePreset';
    name: string;
    mode: string;
    solidSelection: Array<string> | null;
    runConfigYaml: string;
    tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
  }>;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
};

export type LaunchpadSessionRunConfigSchemaFragment_InvalidSubsetError = {
  __typename: 'InvalidSubsetError';
};

export type LaunchpadSessionRunConfigSchemaFragment_ModeNotFoundError = {
  __typename: 'ModeNotFoundError';
  message: string;
};

export type LaunchpadSessionRunConfigSchemaFragment_PipelineNotFoundError = {
  __typename: 'PipelineNotFoundError';
};

export type LaunchpadSessionRunConfigSchemaFragment_PythonError = {__typename: 'PythonError'};

export type LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema = {
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
  | LaunchpadSessionRunConfigSchemaFragment_InvalidSubsetError
  | LaunchpadSessionRunConfigSchemaFragment_ModeNotFoundError
  | LaunchpadSessionRunConfigSchemaFragment_PipelineNotFoundError
  | LaunchpadSessionRunConfigSchemaFragment_PythonError
  | LaunchpadSessionRunConfigSchemaFragment_RunConfigSchema;

export type LaunchpadSessionModeNotFoundFragment = {
  __typename: 'ModeNotFoundError';
  message: string;
};

export const LaunchpadRootQueryVersion = '527627287343c3a482b43445b66c55de58b667dadb36218161575caffbc78348';
