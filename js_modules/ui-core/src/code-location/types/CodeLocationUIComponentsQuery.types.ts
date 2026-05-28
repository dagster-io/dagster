// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type UiComponentFragment = {
  __typename: 'UIComponent';
  componentId: string;
  componentType: string;
  attributes: string;
};

export type CodeLocationUiComponentsQueryVariables = Types.Exact<{
  locationName: Types.Scalars['String']['input'];
}>;

export type CodeLocationUiComponentsQuery = {
  __typename: 'Query';
  uiComponentsForLocationOrError:
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
        __typename: 'UIComponents';
        locationName: string;
        components: Array<{
          __typename: 'UIComponent';
          componentId: string;
          componentType: string;
          attributes: string;
        }>;
      };
};

export type SetUiComponentMutationVariables = Types.Exact<{
  locationName: Types.Scalars['String']['input'];
  componentId: Types.Scalars['String']['input'];
  componentType: Types.Scalars['String']['input'];
  attributes: Types.Scalars['String']['input'];
}>;

export type SetUiComponentMutation = {
  __typename: 'Mutation';
  setUIComponent:
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
        __typename: 'SetUIComponentSuccess';
        component: {
          __typename: 'UIComponent';
          componentId: string;
          componentType: string;
          attributes: string;
        };
      }
    | {__typename: 'UnauthorizedError'; message: string};
};

export type DeleteUiComponentMutationVariables = Types.Exact<{
  locationName: Types.Scalars['String']['input'];
  componentId: Types.Scalars['String']['input'];
}>;

export type DeleteUiComponentMutation = {
  __typename: 'Mutation';
  deleteUIComponent:
    | {__typename: 'DeleteUIComponentSuccess'; locationName: string; componentId: string}
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

export const DeleteVersion = '3c61c79b99122910e754a8863e80dc5ed479a0c23cc1a9d9878d91e603fc0dfe';
