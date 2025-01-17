import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {Meta} from '@storybook/react';
import {MemoryRouter} from 'react-router-dom';

import {
  buildAssetCheckNeedsAgentUpgradeError,
  buildAssetCheckNeedsMigrationError,
  buildAssetCheckNeedsUserCodeUpgrade,
  buildAssetChecks,
  buildAssetKey,
  buildAssetNode,
} from '../../../graphql/types';
import {AssetFeatureProvider} from '../../AssetFeatureContext';
import {buildQueryMock} from '../../AutoMaterializePolicyPage/__fixtures__/AutoMaterializePolicyPage.fixtures';
import {ASSET_CHECK_DETAILS_QUERY} from '../AssetCheckDetailDialog';
import {AssetChecks} from '../AssetChecks';
import {ASSET_CHECKS_QUERY} from '../AssetChecksQuery';
import {
  TestAssetCheck,
  TestAssetCheckWarning,
  testAssetKey,
  testLatestMaterializationTimeStamp,
} from '../__fixtures__/AssetChecks.fixtures';
import {AssetCheckDetailsQueryVariables} from '../types/AssetCheckDetailDialog.types';
import {AssetChecksQueryVariables} from '../types/AssetChecksQuery.types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Checks',
  component: AssetChecks,
} as Meta;

const Component = ({mocks}: {mocks: MockedResponse[]}) => {
  return (
    <MemoryRouter>
      <MockedProvider mocks={mocks}>
        <AssetFeatureProvider>
          <AssetChecks
            assetKey={testAssetKey}
            lastMaterializationTimestamp={testLatestMaterializationTimeStamp.toString()}
          />
        </AssetFeatureProvider>
      </MockedProvider>
    </MemoryRouter>
  );
};

export const MigrationRequired = () => {
  return (
    <Component
      mocks={[
        buildQueryMock<any, AssetChecksQueryVariables>({
          query: ASSET_CHECKS_QUERY,
          variables: {assetKey: testAssetKey},
          data: {
            assetNodeOrError: buildAssetNode({
              assetKey: buildAssetKey(testAssetKey),
              assetChecksOrError: buildAssetCheckNeedsMigrationError(),
            }),
          },
        }),
      ]}
    />
  );
};

export const AgentUpgradeRequired = () => {
  return (
    <Component
      mocks={[
        buildQueryMock<any, AssetChecksQueryVariables>({
          query: ASSET_CHECKS_QUERY,
          variables: {assetKey: testAssetKey},
          data: {
            assetNodeOrError: buildAssetNode({
              assetKey: buildAssetKey(testAssetKey),
              assetChecksOrError: buildAssetCheckNeedsAgentUpgradeError(),
            }),
          },
        }),
      ]}
    />
  );
};

export const NeedsUserCodeUpgradeRequired = () => {
  return (
    <Component
      mocks={[
        buildQueryMock<any, AssetChecksQueryVariables>({
          query: ASSET_CHECKS_QUERY,
          variables: {assetKey: testAssetKey},
          data: {
            assetNodeOrError: buildAssetNode({
              assetKey: buildAssetKey(testAssetKey),
              assetChecksOrError: buildAssetCheckNeedsUserCodeUpgrade(),
            }),
          },
        }),
      ]}
    />
  );
};

export const NoChecks = () => {
  return (
    <Component
      mocks={[
        buildQueryMock<any, AssetChecksQueryVariables>({
          query: ASSET_CHECKS_QUERY,
          variables: {assetKey: testAssetKey},
          data: {
            assetNodeOrError: buildAssetNode({
              assetKey: buildAssetKey(testAssetKey),
              assetChecksOrError: buildAssetChecks({
                checks: [],
              }),
            }),
          },
        }),
      ]}
    />
  );
};

export const Default = () => {
  return (
    <Component
      mocks={[
        buildQueryMock<any, AssetChecksQueryVariables>({
          query: ASSET_CHECKS_QUERY,
          variables: {assetKey: testAssetKey},
          data: {
            assetNodeOrError: buildAssetNode({
              assetKey: buildAssetKey(testAssetKey),
              assetChecksOrError: buildAssetChecks({
                checks: [
                  TestAssetCheck,
                  TestAssetCheckWarning,
                  TestAssetCheck,
                  TestAssetCheck,
                  TestAssetCheck,
                  TestAssetCheck,
                ],
              }),
            }),
          },
        }),
        buildQueryMock<any, AssetCheckDetailsQueryVariables>({
          query: ASSET_CHECK_DETAILS_QUERY,
          variables: {
            assetKey: testAssetKey,
            checkName: 'Test check',
            limit: 6,
          },
          data: {
            assetCheckExecutions: [TestAssetCheck.executionForLatestMaterialization],
          },
        }),
      ]}
    />
  );
};
