import {MockedProvider} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {AssetKeyInput} from '../../graphql/types';
import {AssetView} from '../AssetView';
import {
  AssetViewDefinitionSourceAsset,
  AssetViewDefinitionNonSDA,
  LatestMaterializationTimestamp,
  AssetViewDefinitionSDA,
  AssetGraphEmpty,
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
      await waitFor(async () => {
        expect(screen.queryByText('Materialize')).toBeVisible();
      });
    });

    it('shows the "Observe" button for a software-defined source asset', async () => {
      render(
        <Test path="/observable_source_asset" assetKey={{path: ['observable_source_asset']}} />,
      );
      await waitFor(async () => {
        expect(screen.queryByText('Observe')).toBeVisible();
      });
    });

    it('shows no button for a non-software defined asset', async () => {
      render(<Test path="/non_sda_asset" assetKey={{path: ['non_sda_asset']}} />);
      expect(screen.queryByText('Observe')).toBeNull();
      expect(screen.queryByText('Materialize')).toBeNull();
    });
  });

  describe('Historical view alert', () => {
    it('shows historical view alert if `asOf` is old', async () => {
      await act(async () => {
        render(<Test path="/non_sda_asset?asOf=10" assetKey={{path: ['non_sda_asset']}} />);
      });
      expect(screen.queryByText(MESSAGE)).toBeVisible();
    });

    it('does not show historical view alert if `asOf` is past latest materialization', async () => {
      await act(async () => {
        render(
          <Test
            path={`/non_sda_asset?asOf=${Number(LatestMaterializationTimestamp) + 1000}`}
            assetKey={{path: ['non_sda_asset']}}
          />,
        );
      });
      expect(screen.queryByText(MESSAGE)).toBeNull();
    });

    it('does not show historical view alert if `asOf` is equal to latest materialization', async () => {
      await act(async () => {
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
      await act(async () => {
        render(<Test path="/non_sda_asset" assetKey={{path: ['non_sda_asset']}} />);
      });
      expect(screen.queryByText(MESSAGE)).toBeNull();
    });
  });
});
