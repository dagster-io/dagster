/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type PythonErrorFragment = {
  __typename: 'PythonError';
  message: string;
  stack: Array<string>;
  errorChain: Array<{
    __typename: 'ErrorChainLink';
    isExplicitLink: boolean;
    error: {__typename: 'PythonError'; message: string; stack: Array<string>};
  }>;
};

export type PythonErrorChainFragment = {
  __typename: 'ErrorChainLink';
  isExplicitLink: boolean;
  error: {__typename: 'PythonError'; message: string; stack: Array<string>};
};
