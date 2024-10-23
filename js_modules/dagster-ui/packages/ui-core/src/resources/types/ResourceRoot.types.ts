// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ResourceDetailsFragment = {
  __typename: 'ResourceDetails';
  name: string;
  description: string | null;
  schedulesUsing: Array<string>;
  sensorsUsing: Array<string>;
  resourceType: string;
  configFields: Array<{
    __typename: 'ConfigTypeField';
    name: string;
    description: string | null;
    configTypeKey: string;
    isRequired: boolean;
    defaultValueAsJson: string | null;
  }>;
  configuredValues: Array<{
    __typename: 'ConfiguredValue';
    key: string;
    value: string;
    type: Types.ConfiguredValueType;
  }>;
  nestedResources: Array<{
    __typename: 'NestedResourceEntry';
    name: string;
    type: Types.NestedResourceType;
    resource: {
      __typename: 'ResourceDetails';
      name: string;
      resourceType: string;
      description: string | null;
    } | null;
  }>;
  parentResources: Array<{
    __typename: 'NestedResourceEntry';
    name: string;
    resource: {
      __typename: 'ResourceDetails';
      name: string;
      resourceType: string;
      description: string | null;
    } | null;
  }>;
  assetKeysUsing: Array<{__typename: 'AssetKey'; path: Array<string>}>;
  jobsOpsUsing: Array<{__typename: 'JobWithOps'; jobName: string; opHandleIDs: Array<string>}>;
};

export type ResourceRootQueryVariables = Types.Exact<{
  resourceSelector: Types.ResourceSelector;
}>;

export type ResourceRootQuery = {
  __typename: 'Query';
  topLevelResourceDetailsOrError:
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
        __typename: 'ResourceDetails';
        name: string;
        description: string | null;
        schedulesUsing: Array<string>;
        sensorsUsing: Array<string>;
        resourceType: string;
        configFields: Array<{
          __typename: 'ConfigTypeField';
          name: string;
          description: string | null;
          configTypeKey: string;
          isRequired: boolean;
          defaultValueAsJson: string | null;
        }>;
        configuredValues: Array<{
          __typename: 'ConfiguredValue';
          key: string;
          value: string;
          type: Types.ConfiguredValueType;
        }>;
        nestedResources: Array<{
          __typename: 'NestedResourceEntry';
          name: string;
          type: Types.NestedResourceType;
          resource: {
            __typename: 'ResourceDetails';
            name: string;
            resourceType: string;
            description: string | null;
          } | null;
        }>;
        parentResources: Array<{
          __typename: 'NestedResourceEntry';
          name: string;
          resource: {
            __typename: 'ResourceDetails';
            name: string;
            resourceType: string;
            description: string | null;
          } | null;
        }>;
        assetKeysUsing: Array<{__typename: 'AssetKey'; path: Array<string>}>;
        jobsOpsUsing: Array<{
          __typename: 'JobWithOps';
          jobName: string;
          opHandleIDs: Array<string>;
        }>;
      }
    | {__typename: 'ResourceNotFoundError'};
};

export const ResourceRootQueryVersion = '43f17e6a448c083d86843c38edbae83098853097a8a7a5f3ef3a3238e3880bff';
