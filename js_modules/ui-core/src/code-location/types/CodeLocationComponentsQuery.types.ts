/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DefsStateManagementType =
  | 'LEGACY_CODE_SERVER_SNAPSHOTS'
  | 'LOCAL_FILESYSTEM'
  | 'VERSIONED_STATE_STORAGE';

export type CodeLocationComponentsQueryVariables = Exact<{
  locationName: string;
}>;

export type CodeLocationComponentsQuery = {
  __typename: 'Query';
  componentsForLocationOrError:
    | {
        __typename: 'Components';
        locationName: string;
        components: Array<{
          __typename: 'Component';
          componentId: string;
          componentType: string;
          isAppManaged: boolean;
          attributes: string | null;
          defsStateKey: string | null;
          defsStateManagementType: Types.DefsStateManagementType | null;
          defsStateInfo: {
            __typename: 'DefsKeyStateInfo';
            version: string;
            createTimestamp: number;
            managementType: Types.DefsStateManagementType;
          } | null;
        }>;
      }
    | {__typename: 'PythonError'; message: string};
};

export const CodeLocationComponentsQueryVersion = 'add1a634edb3d5f2fd85c31b34c8207578c2328119a1448e8bdbd81573790a91';
