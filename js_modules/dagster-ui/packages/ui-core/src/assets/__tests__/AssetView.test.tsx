import {MockedProvider} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {AssetKeyInput} from '../../graphql/types';
import {AssetView} from '../AssetView';
import {
  AssetGraphEmpty,
  AssetViewDefinitionNonSDA,
  AssetViewDefinitionSDA,
  AssetViewDefinitionSourceAsset,
  LatestMaterializationTimestamp,
} from '../__fixtures__/AssetViewDefinition.fixtures';

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../graph/asyncGraphLayout', () => ({}));

// These files must be mocked because useVirtualizer tries to create a ResizeObserver,
// and the component tree fails to mount.
jest.mock('../AssetPartitions', () => ({AssetPartitions: () => <div />}));
jest.mock('../AssetEvents', () => ({AssetEvents: () => <div />}));

describe('AssetView', () => {
  const Test = ({path, assetKey}: {path: string; assetKey: AssetKeyInput}) => {
    return (
      <MockedProvider
        mocks={[
          AssetGraphEmpty,
          AssetViewDefinitionSDA,
          AssetViewDefinitionNonSDA,
          AssetViewDefinitionSourceAsset,
        ]}
      >
        <MemoryRouter initialEntries={[path]}>
          <AssetView assetKey={assetKey} />
        </MemoryRouter>
      </MockedProvider>
    );
  };

  const MESSAGE = /this is a historical view of materializations as of \./i;

  describe('Launch button', () => {
    it('shows the "Materialize" button for a software-defined asset', async () => {
      render(<Test path="/sda_asset" assetKey={{path: ['sda_asset']}} />);
      expect(await screen.findByText('Materialize')).toBeVisible();
    });

    it('shows the "Observe" button for a software-defined source asset', async () => {
      render(
        <Test path="/observable_source_asset" assetKey={{path: ['observable_source_asset']}} />,
      );
      expect(await screen.findByText('Observe')).toBeVisible();
    });

    it('shows no button for a non-software defined asset', async () => {
      render(<Test path="/non_sda_asset" assetKey={{path: ['non_sda_asset']}} />);
      expect(screen.queryByText('Observe')).toBeNull();
      expect(screen.queryByText('Materialize')).toBeNull();
    });
  });

  describe('Historical view alert', () => {
    it('shows historical view alert if `asOf` is old', async () => {
      render(<Test path="/non_sda_asset?asOf=10" assetKey={{path: ['non_sda_asset']}} />);
      expect(await screen.findByText(MESSAGE)).toBeVisible();
    });

    // Test is incorrect. The asset has not materialization timestamp at all.
    // eslint-disable-next-line jest/no-disabled-tests
    it.skip('does not show historical view alert if `asOf` is past latest materialization', async () => {
      // `act` because we're asserting a null state.
      act(() => {
        render(
          <Test
            path={`/non_sda_asset?asOf=${Number(LatestMaterializationTimestamp) + 1000}`}
            assetKey={{path: ['non_sda_asset']}}
          />,
        );
      });
      await waitFor(() => {
        expect(screen.queryByText(MESSAGE)).toBeNull();
      });
    });

    // Test is incorrect. The asset has not materialization timestamp at all.
    // eslint-disable-next-line jest/no-disabled-tests
    it.skip('does not show historical view alert if `asOf` is equal to latest materialization', async () => {
      // `act` because we're asserting a null state.
      act(() => {
        render(
          <Test
            path={`/non_sda_asset?asOf=${LatestMaterializationTimestamp}`}
            assetKey={{path: ['non_sda_asset']}}
          />,
        );
      });
      expect(screen.queryByText(MESSAGE)).toBeNull();
    });

    it('does not show historical view alert if no `asOf` is specified', async () => {
      // `act` because we're asserting a null state.
      act(() => {
        render(<Test path="/non_sda_asset" assetKey={{path: ['non_sda_asset']}} />);
      });
      expect(screen.queryByText(MESSAGE)).toBeNull();
    });
  });
});
