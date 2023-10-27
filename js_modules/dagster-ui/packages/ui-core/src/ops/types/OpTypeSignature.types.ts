// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type OpTypeSignatureFragment_CompositeSolidDefinition_ = {
  __typename: 'CompositeSolidDefinition';
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

export type OpTypeSignatureFragment_SolidDefinition_ = {
  __typename: 'SolidDefinition';
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

export type OpTypeSignatureFragment =
  | OpTypeSignatureFragment_CompositeSolidDefinition_
  | OpTypeSignatureFragment_SolidDefinition_;
