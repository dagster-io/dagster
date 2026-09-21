/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AppManagedComponentFragment = {
  __typename: 'AppManagedComponent';
  componentId: string;
  componentType: string;
  attributes: string;
};

export type CodeLocationAppManagedComponentsQueryVariables = Exact<{
  locationName: string;
}>;

export type CodeLocationAppManagedComponentsQuery = {
  __typename: 'Query';
  appManagedComponentsForLocationOrError:
    | {
        __typename: 'AppManagedComponents';
        locationName: string;
        components: Array<{
          __typename: 'AppManagedComponent';
          componentId: string;
          componentType: string;
          attributes: string;
        }>;
      }
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

export type SetAppManagedComponentMutationVariables = Exact<{
  locationName: string;
  componentId: string;
  componentType: string;
  attributes: string;
}>;

export type SetAppManagedComponentMutation = {
  __typename: 'Mutation';
  setAppManagedComponent:
    | {__typename: 'AppManagedComponentValidationError'; message: string; errors: Array<string>}
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
        __typename: 'SetAppManagedComponentSuccess';
        component: {
          __typename: 'AppManagedComponent';
          componentId: string;
          componentType: string;
          attributes: string;
        };
      }
    | {__typename: 'UnauthorizedError'; message: string};
};

export type DeleteAppManagedComponentMutationVariables = Exact<{
  locationName: string;
  componentId: string;
}>;

export type DeleteAppManagedComponentMutation = {
  __typename: 'Mutation';
  deleteAppManagedComponent:
    | {__typename: 'DeleteAppManagedComponentSuccess'; locationName: string; componentId: string}
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
    | {__typename: 'UnauthorizedError'; message: string};
};

export const CodeLocationAppManagedComponentsQueryVersion = '590944ed746ac52a5ec6df0069d26319cc5ef1d070546f71f09b0223c4a35320';

export const SetAppManagedComponentMutationVersion = '4726d60bf6eb5b88f136c1541326eb36bc3706177a7bcd162d0cdac134d09786';

export const DeleteAppManagedComponentMutationVersion = '3db9b7817d9c4742d00c9e70dd6e270853d5668d5640d41b05411659bbf61bd4';

export const DeleteVersion = '3c61c79b99122910e754a8863e80dc5ed479a0c23cc1a9d9878d91e603fc0dfe';
