// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type OpsRootQueryVariables = Types.Exact<{
  repositorySelector: Types.RepositorySelector;
}>;

export type OpsRootQuery = {
  __typename: 'Query';
  repositoryOrError:
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
        __typename: 'Repository';
        id: string;
        usedSolids: Array<{
          __typename: 'UsedSolid';
          definition:
            | {
                __typename: 'CompositeSolidDefinition';
                name: string;
                outputDefinitions: Array<{
                  __typename: 'OutputDefinition';
                  name: string;
                  type:
                    | {
                        __typename: 'ListDagsterType';
                        name: string | null;
                        displayName: string;
                        description: string | null;
                      }
                    | {
                        __typename: 'NullableDagsterType';
                        name: string | null;
                        displayName: string;
                        description: string | null;
                      }
                    | {
                        __typename: 'RegularDagsterType';
                        name: string | null;
                        displayName: string;
                        description: string | null;
                      };
                }>;
                inputDefinitions: Array<{
                  __typename: 'InputDefinition';
                  name: string;
                  type:
                    | {
                        __typename: 'ListDagsterType';
                        name: string | null;
                        displayName: string;
                        description: string | null;
                      }
                    | {
                        __typename: 'NullableDagsterType';
                        name: string | null;
                        displayName: string;
                        description: string | null;
                      }
                    | {
                        __typename: 'RegularDagsterType';
                        name: string | null;
                        displayName: string;
                        description: string | null;
                      };
                }>;
              }
            | {
                __typename: 'SolidDefinition';
                name: string;
                outputDefinitions: Array<{
                  __typename: 'OutputDefinition';
                  name: string;
                  type:
                    | {
                        __typename: 'ListDagsterType';
                        name: string | null;
                        displayName: string;
                        description: string | null;
                      }
                    | {
                        __typename: 'NullableDagsterType';
                        name: string | null;
                        displayName: string;
                        description: string | null;
                      }
                    | {
                        __typename: 'RegularDagsterType';
                        name: string | null;
                        displayName: string;
                        description: string | null;
                      };
                }>;
                inputDefinitions: Array<{
                  __typename: 'InputDefinition';
                  name: string;
                  type:
                    | {
                        __typename: 'ListDagsterType';
                        name: string | null;
                        displayName: string;
                        description: string | null;
                      }
                    | {
                        __typename: 'NullableDagsterType';
                        name: string | null;
                        displayName: string;
                        description: string | null;
                      }
                    | {
                        __typename: 'RegularDagsterType';
                        name: string | null;
                        displayName: string;
                        description: string | null;
                      };
                }>;
              };
          invocations: Array<{
            __typename: 'NodeInvocationSite';
            pipeline: {__typename: 'Pipeline'; id: string; isJob: boolean; name: string};
          }>;
        }>;
      }
    | {__typename: 'RepositoryNotFoundError'};
};

export type OpsRootUsedSolidFragment = {
  __typename: 'UsedSolid';
  definition:
    | {
        __typename: 'CompositeSolidDefinition';
        name: string;
        outputDefinitions: Array<{
          __typename: 'OutputDefinition';
          name: string;
          type:
            | {
                __typename: 'ListDagsterType';
                name: string | null;
                displayName: string;
                description: string | null;
              }
            | {
                __typename: 'NullableDagsterType';
                name: string | null;
                displayName: string;
                description: string | null;
              }
            | {
                __typename: 'RegularDagsterType';
                name: string | null;
                displayName: string;
                description: string | null;
              };
        }>;
        inputDefinitions: Array<{
          __typename: 'InputDefinition';
          name: string;
          type:
            | {
                __typename: 'ListDagsterType';
                name: string | null;
                displayName: string;
                description: string | null;
              }
            | {
                __typename: 'NullableDagsterType';
                name: string | null;
                displayName: string;
                description: string | null;
              }
            | {
                __typename: 'RegularDagsterType';
                name: string | null;
                displayName: string;
                description: string | null;
              };
        }>;
      }
    | {
        __typename: 'SolidDefinition';
        name: string;
        outputDefinitions: Array<{
          __typename: 'OutputDefinition';
          name: string;
          type:
            | {
                __typename: 'ListDagsterType';
                name: string | null;
                displayName: string;
                description: string | null;
              }
            | {
                __typename: 'NullableDagsterType';
                name: string | null;
                displayName: string;
                description: string | null;
              }
            | {
                __typename: 'RegularDagsterType';
                name: string | null;
                displayName: string;
                description: string | null;
              };
        }>;
        inputDefinitions: Array<{
          __typename: 'InputDefinition';
          name: string;
          type:
            | {
                __typename: 'ListDagsterType';
                name: string | null;
                displayName: string;
                description: string | null;
              }
            | {
                __typename: 'NullableDagsterType';
                name: string | null;
                displayName: string;
                description: string | null;
              }
            | {
                __typename: 'RegularDagsterType';
                name: string | null;
                displayName: string;
                description: string | null;
              };
        }>;
      };
  invocations: Array<{
    __typename: 'NodeInvocationSite';
    pipeline: {__typename: 'Pipeline'; id: string; isJob: boolean; name: string};
  }>;
};

export const OpsRootQueryVersion = 'a8ce0cedc4ebcc5ed0007d8795360ce5635ceefe1882802f88162b457f2058a4';
