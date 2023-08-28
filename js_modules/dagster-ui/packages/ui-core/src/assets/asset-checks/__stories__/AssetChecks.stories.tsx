import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {Meta} from '@storybook/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {buildAssetCheckNeedsMigrationError, buildAssetChecks} from '../../../graphql/types';
import {buildQueryMock} from '../../AutoMaterializePolicyPage/__fixtures__/AutoMaterializePolicyPage.fixtures';
import {ASSET_CHECKS_QUERY, AssetChecks} from '../AssetChecks';
import {
  TestAssetCheck,
  testAssetKey,
  testLatestMaterializationTimeStamp,
  testLatestMaterializationRunId,
  TestAssetCheckWarning,
} from '../__fixtures__/AssetChecks.fixtures';
import {AssetChecksQuery, AssetChecksQueryVariables} from '../types/AssetChecks.types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'AssetChecks',
  component: AssetChecks,
} as Meta;

const Component = ({mocks}: {mocks: MockedResponse[]}) => {
  return (
    <MemoryRouter>
      <MockedProvider mocks={mocks}>
        <AssetChecks
          assetKey={testAssetKey}
          lastMaterializationTimestamp={testLatestMaterializationTimeStamp.toString()}
          lastMaterializationRunId={testLatestMaterializationRunId.toString()}
        />
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
          },
        }),
      ]}
    />
  );
};
