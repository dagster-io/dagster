// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SidebarOpRepositoryFragment = {
  __typename: 'Repository';
  id: string;
  name: string;
  displayMetadata: Array<{__typename: 'RepositoryMetadata'; key: string; value: string}>;
};

export type SidebarOpInvocationFragment = {
  __typename: 'Solid';
  name: string;
  inputs: Array<{
    __typename: 'Input';
    isDynamicCollect: boolean;
    definition: {
      __typename: 'InputDefinition';
      name: string;
      description: string | null;
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
    };
    dependsOn: Array<{
      __typename: 'Output';
      definition: {__typename: 'OutputDefinition'; name: string};
      solid: {__typename: 'Solid'; name: string};
    }>;
  }>;
  outputs: Array<{
    __typename: 'Output';
    definition: {
      __typename: 'OutputDefinition';
      name: string;
      description: string | null;
      isDynamic: boolean | null;
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
    };
    dependedBy: Array<{
      __typename: 'Input';
      definition: {__typename: 'InputDefinition'; name: string};
      solid: {__typename: 'Solid'; name: string};
    }>;
  }>;
  definition:
    | {
        __typename: 'CompositeSolidDefinition';
        metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
      }
    | {
        __typename: 'SolidDefinition';
        metadata: Array<{__typename: 'MetadataItemDefinition'; key: string; value: string}>;
      };
};
