import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {Meta} from '@storybook/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {
  buildAssetCheckNeedsMigrationError,
  buildAssetChecks,
  buildAssetKey,
  buildAssetNode,
} from '../../../graphql/types';
import {AssetFeatureProvider} from '../../AssetFeatureContext';
import {buildQueryMock} from '../../AutoMaterializePolicyPage/__fixtures__/AutoMaterializePolicyPage.fixtures';
import {ASSET_CHECK_DETAILS_QUERY} from '../AssetCheckDetailModal';
import {ASSET_CHECKS_QUERY, AssetChecks} from '../AssetChecks';
import {
  TestAssetCheck,
  testAssetKey,
  testLatestMaterializationTimeStamp,
  TestAssetCheckWarning,
  TestAssetCheckNoExecutions,
} from '../__fixtures__/AssetChecks.fixtures';
import {
  AssetCheckDetailsQuery,
  AssetCheckDetailsQueryVariables,
} from '../types/AssetCheckDetailModal.types';
import {AssetChecksQuery, AssetChecksQueryVariables} from '../types/AssetChecks.types';

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
        buildQueryMock<AssetChecksQuery, AssetChecksQueryVariables>({
          query: ASSET_CHECKS_QUERY,
          variables: {assetKey: testAssetKey},
          data: {
            assetChecksOrError: buildAssetCheckNeedsMigrationError(),
            assetNodeOrError: buildAssetNode({
              assetKey: buildAssetKey(testAssetKey),
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
        buildQueryMock<AssetChecksQuery, AssetChecksQueryVariables>({
          query: ASSET_CHECKS_QUERY,
          variables: {assetKey: testAssetKey},
          data: {
            assetChecksOrError: buildAssetChecks({
              checks: [],
            }) as any,
            assetNodeOrError: buildAssetNode({
              assetKey: buildAssetKey(testAssetKey),
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
        buildQueryMock<AssetChecksQuery, AssetChecksQueryVariables>({
          query: ASSET_CHECKS_QUERY,
          variables: {assetKey: testAssetKey},
          data: {
            assetChecksOrError: buildAssetChecks({
              checks: [
                TestAssetCheck,
                TestAssetCheckWarning,
                TestAssetCheck,
                TestAssetCheck,
                TestAssetCheck,
                TestAssetCheck,
              ],
            }) as any,
            assetNodeOrError: buildAssetNode({
              assetKey: buildAssetKey(testAssetKey),
            }),
          },
        }),
        buildQueryMock<AssetCheckDetailsQuery, AssetCheckDetailsQueryVariables>({
          query: ASSET_CHECK_DETAILS_QUERY,
          variables: {
            assetKey: testAssetKey,
            checkName: 'Test check',
            limit: 6,
          },
          data: {
            assetChecksOrError: buildAssetChecks({
              checks: [TestAssetCheckNoExecutions],
            }) as any,
          },
        }),
      ]}
    />
  );
};
