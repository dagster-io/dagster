import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {tokenForAssetKey} from '../../asset-graph/Utils';
import {
  buildAssetHealth,
  buildAssetHealthMaterializationWarningNotPartitionedMeta,
  buildAssetHealthMaterializationWarningPartitionedMeta,
  buildAssetKey,
} from '../../graphql/builders';
import {AssetHealthStatus} from '../../graphql/types';

// Mock useAllAssetsNodes
const mockUseAllAssetsNodes = jest.fn();
jest.mock('../useAllAssets', () => ({
  useAllAssetsNodes: mockUseAllAssetsNodes,
}));

// Mock useAssetHealthData
const mockUseAssetHealthData = jest.fn();
jest.mock('../../asset-data/AssetHealthDataProvider', () => ({
  useAssetHealthData: mockUseAssetHealthData,
}));

// Mock useTrackEvent
const mockUseTrackEvent = jest.fn();
jest.mock('../../app/analytics', () => ({
  useTrackEvent: mockUseTrackEvent,
}));

describe('AssetHealthSummary integration tests', () => {
  let AssetHealthSummaryPopover: React.ComponentType<{
    assetKey: ReturnType<typeof buildAssetKey>;
    health?: ReturnType<typeof buildAssetHealth>;
    children: React.ReactNode;
  }>;

  beforeAll(() => {
    // Import this after mocks are setup
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const module = require('../AssetHealthSummary');
    AssetHealthSummaryPopover = module.AssetHealthSummaryPopover;
  });

  beforeEach(() => {
    mockUseTrackEvent.mockReturnValue(jest.fn());
    mockUseAssetHealthData.mockReturnValue({
      liveData: null,
      loading: false,
      error: null,
    });
    mockUseAllAssetsNodes.mockReturnValue({
      allAssetKeys: new Set(),
      loading: false,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('no-definition behavior', () => {
    it('should show missing software definition for assets without definitions', async () => {
      const user = userEvent.setup();
      const assetKey = buildAssetKey({path: ['missing_asset']});

      // Mock that this asset is not in the workspace
      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set(), // Empty set means no definitions
        loading: false,
      });

      mockUseAssetHealthData.mockReturnValue({
        liveData: {
          assetHealth: null,
        },
        loading: false,
        error: null,
      });

      render(
        <MockedProvider>
          <AssetHealthSummaryPopover assetKey={assetKey}>
            <div>Trigger</div>
          </AssetHealthSummaryPopover>
        </MockedProvider>,
      );

      // Hover over the trigger to show popover
      await user.hover(screen.getByText('Trigger'));

      await waitFor(() => {
        expect(screen.getByText('Missing software definition')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(
          screen.getByText(
            'It may have been deleted or be a stub imported through an integration.',
          ),
        ).toBeInTheDocument();
      });
    });

    it('should show normal health criteria for assets with definitions', async () => {
      const user = userEvent.setup();
      const assetKey = buildAssetKey({path: ['existing_asset']});

      // Mock that this asset is in the workspace
      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set([tokenForAssetKey(assetKey)]),
        loading: false,
      });

      mockUseAssetHealthData.mockReturnValue({
        liveData: {
          assetHealth: {
            materializationStatus: 'HEALTHY',
            freshnessStatus: 'HEALTHY',
            assetChecksStatus: 'HEALTHY',
            materializationStatusMetadata: null,
            freshnessStatusMetadata: null,
            assetChecksStatusMetadata: null,
          },
        },
        loading: false,
        error: null,
      });

      render(
        <MockedProvider>
          <AssetHealthSummaryPopover assetKey={assetKey}>
            <div>Trigger</div>
          </AssetHealthSummaryPopover>
        </MockedProvider>,
      );

      // Hover over the trigger to show popover
      await user.hover(screen.getByText('Trigger'));

      await waitFor(() => {
        // Should show the standard criteria instead of missing definition
        expect(screen.queryByText('Missing software definition')).not.toBeInTheDocument();
      });
    });

    it('should wait for loading to complete before showing no-definition message', async () => {
      const user = userEvent.setup();
      const assetKey = buildAssetKey({path: ['loading_asset']});

      // Mock loading state
      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set(),
        loading: true, // Still loading
      });

      render(
        <MockedProvider>
          <AssetHealthSummaryPopover assetKey={assetKey}>
            <div>Trigger</div>
          </AssetHealthSummaryPopover>
        </MockedProvider>,
      );

      // Hover over the trigger to show popover
      await user.hover(screen.getByText('Trigger'));

      // Should show normal criteria while loading, not the no-definition message
      await waitFor(() => {
        expect(screen.queryByText('Missing software definition')).not.toBeInTheDocument();
      });
    });

    it('should handle asset key that transitions from loading to no-definition', async () => {
      const user = userEvent.setup();
      const assetKey = buildAssetKey({path: ['transitioning_asset']});

      // Start with loading state
      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set(),
        loading: true,
      });

      const {rerender} = render(
        <MockedProvider>
          <AssetHealthSummaryPopover assetKey={assetKey}>
            <div>Trigger</div>
          </AssetHealthSummaryPopover>
        </MockedProvider>,
      );

      // Hover over the trigger to show popover
      await user.hover(screen.getByText('Trigger'));

      // Should not show no-definition message while loading
      await waitFor(() => {
        expect(screen.queryByText('Missing software definition')).not.toBeInTheDocument();
      });

      // Update to finished loading with no definitions
      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set(),
        loading: false,
      });

      rerender(
        <MockedProvider>
          <AssetHealthSummaryPopover assetKey={assetKey}>
            <div>Trigger</div>
          </AssetHealthSummaryPopover>
        </MockedProvider>,
      );

      // Now should show the no-definition message
      await waitFor(() => {
        expect(screen.getByText('Missing software definition')).toBeInTheDocument();
      });
    });

    it('should handle complex asset keys correctly', async () => {
      const user = userEvent.setup();
      const assetKey = buildAssetKey({path: ['namespace', 'complex', 'asset_name']});

      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set(), // Asset not in definitions
        loading: false,
      });

      render(
        <MockedProvider>
          <AssetHealthSummaryPopover assetKey={assetKey}>
            <div>Trigger</div>
          </AssetHealthSummaryPopover>
        </MockedProvider>,
      );

      await user.hover(screen.getByText('Trigger'));

      await waitFor(() => {
        expect(screen.getByText('Missing software definition')).toBeInTheDocument();
      });
    });
  });

  describe('up-for-retry warning behavior', () => {
    it('should show retry-pending explanation for a non-partitioned warning asset', async () => {
      const user = userEvent.setup();
      const assetKey = buildAssetKey({path: ['warning_asset']});

      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set([tokenForAssetKey(assetKey)]),
        loading: false,
      });

      const health = buildAssetHealth({
        assetHealth: AssetHealthStatus.WARNING,
        materializationStatus: AssetHealthStatus.WARNING,
        freshnessStatus: AssetHealthStatus.HEALTHY,
        assetChecksStatus: AssetHealthStatus.HEALTHY,
        materializationStatusMetadata: buildAssetHealthMaterializationWarningNotPartitionedMeta({
          failedRunId: 'abcd1234-run-id',
        }),
        freshnessStatusMetadata: null,
        assetChecksStatusMetadata: null,
      });

      render(
        <MemoryRouter>
          <MockedProvider>
            <AssetHealthSummaryPopover assetKey={assetKey} health={health}>
              <div>Trigger</div>
            </AssetHealthSummaryPopover>
          </MockedProvider>
        </MemoryRouter>,
      );

      await user.hover(screen.getByText('Trigger'));

      expect(await screen.findByText('Execution warning')).toBeInTheDocument();
      const link = await screen.findByText(/retry pending/);
      expect(link.closest('a')).toHaveAttribute('href', '/runs/abcd1234-run-id');
    });

    it('should show retry-pending partition counts for a partitioned warning asset', async () => {
      const user = userEvent.setup();
      const assetKey = buildAssetKey({path: ['warning_partitioned_asset']});

      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set([tokenForAssetKey(assetKey)]),
        loading: false,
      });

      const health = buildAssetHealth({
        assetHealth: AssetHealthStatus.WARNING,
        materializationStatus: AssetHealthStatus.WARNING,
        freshnessStatus: AssetHealthStatus.HEALTHY,
        assetChecksStatus: AssetHealthStatus.HEALTHY,
        materializationStatusMetadata: buildAssetHealthMaterializationWarningPartitionedMeta({
          numUpForRetryPartitions: 2,
          numMissingPartitions: 1,
          totalNumPartitions: 5,
        }),
        freshnessStatusMetadata: null,
        assetChecksStatusMetadata: null,
      });

      render(
        <MemoryRouter>
          <MockedProvider>
            <AssetHealthSummaryPopover assetKey={assetKey} health={health}>
              <div>Trigger</div>
            </AssetHealthSummaryPopover>
          </MockedProvider>
        </MemoryRouter>,
      );

      await user.hover(screen.getByText('Trigger'));

      const link = await screen.findByText(/retries pending/);
      expect(link.textContent).toContain('2 out of 5 partitions, retries pending');
    });

    it('should render without a detail line when the metadata type is unknown to this bundle', async () => {
      const user = userEvent.setup();
      const assetKey = buildAssetKey({path: ['warning_asset_new_meta']});

      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set([tokenForAssetKey(assetKey)]),
        loading: false,
      });

      const health = buildAssetHealth({
        assetHealth: AssetHealthStatus.WARNING,
        materializationStatus: AssetHealthStatus.WARNING,
        freshnessStatus: AssetHealthStatus.HEALTHY,
        assetChecksStatus: AssetHealthStatus.HEALTHY,
        // Simulates a newer server returning a union member this bundle was not built with.
        materializationStatusMetadata: {
          __typename: 'AssetHealthMaterializationFutureMeta',
        } as unknown as ReturnType<typeof buildAssetHealthMaterializationWarningNotPartitionedMeta>,
        freshnessStatusMetadata: null,
        assetChecksStatusMetadata: null,
      });

      render(
        <MemoryRouter>
          <MockedProvider>
            <AssetHealthSummaryPopover assetKey={assetKey} health={health}>
              <div>Trigger</div>
            </AssetHealthSummaryPopover>
          </MockedProvider>
        </MemoryRouter>,
      );

      await user.hover(screen.getByText('Trigger'));

      expect(await screen.findByText('Execution warning')).toBeInTheDocument();
      expect(screen.queryByText(/retry pending/)).not.toBeInTheDocument();
    });
  });

  describe('styling and layout', () => {
    it('should apply correct maxWidth styling for criteria', async () => {
      const user = userEvent.setup();
      const assetKey = buildAssetKey({path: ['styled_asset']});

      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set(),
        loading: false,
      });

      mockUseAssetHealthData.mockReturnValue({
        liveData: {
          assetHealth: null,
        },
        loading: false,
        error: null,
      });

      render(
        <MockedProvider>
          <AssetHealthSummaryPopover assetKey={assetKey}>
            <div>Trigger</div>
          </AssetHealthSummaryPopover>
        </MockedProvider>,
      );

      await user.hover(screen.getByText('Trigger'));

      await waitFor(() => {
        const criteriaElement = screen.getByText('Missing software definition').closest('div');
        expect(criteriaElement).toHaveStyle({maxWidth: '300px'});
      });
    });

    it('should maintain full opacity for no-definition criteria', async () => {
      const user = userEvent.setup();
      const assetKey = buildAssetKey({path: ['dim_asset']});

      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set(),
        loading: false,
      });

      render(
        <MockedProvider>
          <AssetHealthSummaryPopover assetKey={assetKey}>
            <div>Trigger</div>
          </AssetHealthSummaryPopover>
        </MockedProvider>,
      );

      await user.hover(screen.getByText('Trigger'));

      await waitFor(() => {
        const criteriaElement = screen.getByText('Missing software definition').closest('div');
        expect(criteriaElement).toHaveStyle({opacity: '1'});
      });
    });
  });

  describe('explanation text', () => {
    it('should show correct explanation text for no-definition case', async () => {
      const user = userEvent.setup();
      const assetKey = buildAssetKey({path: ['explanation_asset']});

      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set(),
        loading: false,
      });

      render(
        <MockedProvider>
          <AssetHealthSummaryPopover assetKey={assetKey}>
            <div>Trigger</div>
          </AssetHealthSummaryPopover>
        </MockedProvider>,
      );

      await user.hover(screen.getByText('Trigger'));

      await waitFor(() => {
        expect(
          screen.getByText(
            'It may have been deleted or be a stub imported through an integration.',
          ),
        ).toBeInTheDocument();
      });
    });
  });
});
