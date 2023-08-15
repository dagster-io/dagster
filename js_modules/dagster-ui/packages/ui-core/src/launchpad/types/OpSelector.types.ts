// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type OpSelectorQueryVariables = Types.Exact<{
  selector: Types.PipelineSelector;
  requestScopeHandleID?: Types.InputMaybe<Types.Scalars['String']>;
}>;

export type OpSelectorQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'; message: string}
    | {
        __typename: 'Pipeline';
        id: string;
        name: string;
        solidHandles: Array<{
          __typename: 'SolidHandle';
          handleID: string;
          solid: {
            __typename: 'Solid';
            name: string;
            isDynamicMapped: boolean;
            definition:
              | {
                  __typename: 'CompositeSolidDefinition';
                  name: string;
                  id: string;
                  description: string | null;
                  inputMappings: Array<{
                    __typename: 'InputMapping';
                    definition: {__typename: 'InputDefinition'; name: string};
                    mappedInput: {
                      __typename: 'Input';
                      definition: {__typename: 'InputDefinition'; name: string};
                      solid: {__typename: 'Solid'; name: string};
                    };
                  }>;
                  outputMappings: Array<{
                    __typename: 'OutputMapping';
                    definition: {__typename: 'OutputDefinition'; name: string};
                    mappedOutput: {
                      __typename: 'Output';
                      definition: {__typename: 'OutputDefinition'; name: string};
                      solid: {__typename: 'Solid'; name: string};
                    };
                  }>;
                  metadata: Array<{
                    __typename: 'MetadataItemDefinition';
                    key: string;
                    value: string;
                  }>;
                  assetNodes: Array<{
                    __typename: 'AssetNode';
                    id: string;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }>;
                  inputDefinitions: Array<{
                    __typename: 'InputDefinition';
                    name: string;
                    type:
                      | {__typename: 'ListDagsterType'; displayName: string}
                      | {__typename: 'NullableDagsterType'; displayName: string}
                      | {__typename: 'RegularDagsterType'; displayName: string};
                  }>;
                  outputDefinitions: Array<{
                    __typename: 'OutputDefinition';
                    name: string;
                    isDynamic: boolean | null;
                    type:
                      | {__typename: 'ListDagsterType'; displayName: string}
                      | {__typename: 'NullableDagsterType'; displayName: string}
                      | {__typename: 'RegularDagsterType'; displayName: string};
                  }>;
                }
              | {
                  __typename: 'SolidDefinition';
                  name: string;
                  description: string | null;
                  configField: {
                    __typename: 'ConfigTypeField';
                    configType:
                      | {__typename: 'ArrayConfigType'; key: string; description: string | null}
                      | {__typename: 'CompositeConfigType'; key: string; description: string | null}
                      | {__typename: 'EnumConfigType'; key: string; description: string | null}
                      | {__typename: 'MapConfigType'; key: string; description: string | null}
                      | {__typename: 'NullableConfigType'; key: string; description: string | null}
                      | {__typename: 'RegularConfigType'; key: string; description: string | null}
                      | {
                          __typename: 'ScalarUnionConfigType';
                          key: string;
                          description: string | null;
                        };
                  } | null;
                  metadata: Array<{
                    __typename: 'MetadataItemDefinition';
                    key: string;
                    value: string;
                  }>;
                  assetNodes: Array<{
                    __typename: 'AssetNode';
                    id: string;
                    assetKey: {__typename: 'AssetKey'; path: Array<string>};
                  }>;
                  inputDefinitions: Array<{
                    __typename: 'InputDefinition';
                    name: string;
                    type:
                      | {__typename: 'ListDagsterType'; displayName: string}
                      | {__typename: 'NullableDagsterType'; displayName: string}
                      | {__typename: 'RegularDagsterType'; displayName: string};
                  }>;
                  outputDefinitions: Array<{
                    __typename: 'OutputDefinition';
                    name: string;
                    isDynamic: boolean | null;
                    type:
                      | {__typename: 'ListDagsterType'; displayName: string}
                      | {__typename: 'NullableDagsterType'; displayName: string}
                      | {__typename: 'RegularDagsterType'; displayName: string};
                  }>;
                };
            inputs: Array<{
              __typename: 'Input';
              isDynamicCollect: boolean;
              definition: {__typename: 'InputDefinition'; name: string};
              dependsOn: Array<{
                __typename: 'Output';
                definition: {
                  __typename: 'OutputDefinition';
                  name: string;
                  type:
                    | {__typename: 'ListDagsterType'; displayName: string}
                    | {__typename: 'NullableDagsterType'; displayName: string}
                    | {__typename: 'RegularDagsterType'; displayName: string};
                };
                solid: {__typename: 'Solid'; name: string};
              }>;
            }>;
            outputs: Array<{
              __typename: 'Output';
              definition: {__typename: 'OutputDefinition'; name: string};
              dependedBy: Array<{
                __typename: 'Input';
                solid: {__typename: 'Solid'; name: string};
                definition: {
                  __typename: 'InputDefinition';
                  name: string;
                  type:
                    | {__typename: 'ListDagsterType'; displayName: string}
                    | {__typename: 'NullableDagsterType'; displayName: string}
                    | {__typename: 'RegularDagsterType'; displayName: string};
                };
              }>;
            }>;
          };
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
};
