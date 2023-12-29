import {MockedResponse} from '@apollo/client/testing';

import {buildAssetNode, buildAutoMaterializePolicy, buildSensor} from '../../graphql/types';
import {DUNDER_REPO_NAME} from '../../workspace/buildRepoAddress';
import {ASSET_GROUP_METADATA_QUERY} from '../AssetGroupRoot';
import {
  AssetGroupMetadataQuery,
  AssetGroupMetadataQueryVariables,
} from '../types/AssetGroupRoot.types';

export const GROUP_NAME = 'my_group';
export const LOCATION_NAME = 'my_location';
export const AMP_SENSOR_ID = 'default_automation_sensor';

export const assetGroupWithoutAMP: MockedResponse<
  AssetGroupMetadataQuery,
  AssetGroupMetadataQueryVariables
> = {
  request: {
    query: ASSET_GROUP_METADATA_QUERY,
    variables: {
      selector: {
        groupName: GROUP_NAME,
        repositoryName: DUNDER_REPO_NAME,
        repositoryLocationName: LOCATION_NAME,
      },
    },
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodes: [
        buildAssetNode({
          id: 'node_vanilla',
          autoMaterializePolicy: null,
          automationPolicySensor: null,
        }),
      ],
    },
  },
};

export const assetGroupWithAMP: MockedResponse<
  AssetGroupMetadataQuery,
  AssetGroupMetadataQueryVariables
> = {
  request: {
    query: ASSET_GROUP_METADATA_QUERY,
    variables: {
      selector: {
        groupName: GROUP_NAME,
        repositoryName: DUNDER_REPO_NAME,
        repositoryLocationName: LOCATION_NAME,
      },
    },
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodes: [
        buildAssetNode({
          id: 'node_with_amp',
          autoMaterializePolicy: buildAutoMaterializePolicy(),
          automationPolicySensor: null,
        }),
      ],
    },
  },
};

export const assetGroupWithAMPSensor: MockedResponse<
  AssetGroupMetadataQuery,
  AssetGroupMetadataQueryVariables
> = {
  request: {
    query: ASSET_GROUP_METADATA_QUERY,
    variables: {
      selector: {
        groupName: GROUP_NAME,
        repositoryName: DUNDER_REPO_NAME,
        repositoryLocationName: LOCATION_NAME,
      },
    },
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodes: [
        buildAssetNode({
          id: 'node_with_amp_sensor',
          autoMaterializePolicy: null,
          automationPolicySensor: buildSensor({
            id: AMP_SENSOR_ID,
            name: AMP_SENSOR_ID,
          }),
        }),
      ],
    },
  },
};

export const assetGroupWithManyAMPSensors: MockedResponse<
  AssetGroupMetadataQuery,
  AssetGroupMetadataQueryVariables
> = {
  request: {
    query: ASSET_GROUP_METADATA_QUERY,
    variables: {
      selector: {
        groupName: GROUP_NAME,
        repositoryName: DUNDER_REPO_NAME,
        repositoryLocationName: LOCATION_NAME,
      },
    },
  },
  result: {
    data: {
      __typename: 'Query',
      assetNodes: [
        buildAssetNode({
          id: 'node_with_amp_sensor_a',
          autoMaterializePolicy: null,
          automationPolicySensor: buildSensor({
            id: `${AMP_SENSOR_ID}-A`,
            name: `${AMP_SENSOR_ID}-A`,
          }),
        }),
        buildAssetNode({
          id: 'node_with_amp_sensor_b',
          autoMaterializePolicy: null,
          automationPolicySensor: buildSensor({
            id: `${AMP_SENSOR_ID}-B`,
            name: `${AMP_SENSOR_ID}-B`,
          }),
        }),
        buildAssetNode({
          id: 'node_with_amp_sensor_c',
          autoMaterializePolicy: null,
          automationPolicySensor: buildSensor({
            id: `${AMP_SENSOR_ID}-C`,
            name: `${AMP_SENSOR_ID}-C`,
          }),
        }),
      ],
    },
  },
};
