import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, getByTestId, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import {MemoryRouter, Route} from 'react-router-dom';

import {AssetKeyInput} from '../../graphql/types';
import {AssetPartitionListProps} from '../AssetPartitionList';
import {AssetPartitionStatus} from '../AssetPartitionStatus';
import {AssetPartitions} from '../AssetPartitions';
import {AssetViewParams} from '../AssetView';
import {
  SingleDimensionStaticPartitionHealthQuery,
  SingleDimensionTimePartitionHealthQuery,
  MultiDimensionTimeFirstPartitionHealthQuery,
} from '../__fixtures__/PartitionHealthSummary.fixtures';

jest.setTimeout(20000);

// This file must be mocked because useVirtualizer tries to create a ResizeObserver,
// and the component tree fails to mount. We still want to test whether certain partitions
// are shown, so we print the keys in a simple "list".
jest.mock('../AssetPartitionList', () => ({
  AssetPartitionList: (props: AssetPartitionListProps) => (
    <div>
      <div data-testid="focused-partition">{props.focusedDimensionKey}</div>
      {props.partitions.map((p, index) => (
        <div
          key={p}
          onClick={() => props.setFocusedDimensionKey?.(p)}
          data-testid={`asset-partition-row-${p}-index-${index}`}
        >
          {p}
        </div>
      ))}
    </div>
  ),
}));

const SingleDimensionAssetPartitions: React.FC<{
  assetKey: AssetKeyInput;
  mocks?: MockedResponse[];
}> = ({assetKey, mocks}) => {
  const [params, setParams] = React.useState<AssetViewParams>({});
  return (
    <MemoryRouter>
      <MockedProvider
        mocks={[
          SingleDimensionTimePartitionHealthQuery,
          SingleDimensionStaticPartitionHealthQuery,
          ...(mocks || []),
        ]}
      >
        <AssetPartitions
          assetKey={assetKey}
          params={params}
          setParams={setParams}
          paramsTimeWindowOnly={false}
          assetPartitionDimensions={['default']}
          dataRefreshHint={undefined}
        />
      </MockedProvider>
      <Route
        path="*"
        render={({location}) => <div data-testid="router-search">{location.search}</div>}
      />
    </MemoryRouter>
  );
};

describe('AssetPartitions', () => {
  it('should support filtering a time-partitioned asset to a time range using the top bar', async () => {
    await act(async () => {
      render(<SingleDimensionAssetPartitions assetKey={{path: ['single_dimension_time']}} />);
    });

    await waitFor(() => {
      expect(screen.getByTestId('partitions-selected')).toHaveTextContent('6,000 Partitions');
    });

    const partitionInput = screen.getByTestId('dimension-range-input');
    await userEvent.clear(partitionInput);
    await userEvent.type(partitionInput, '{[}2022-11-28-20:00...2022-12-05-01:00{]}');
    await userEvent.tab();

    await waitFor(() => {
      // Verify that the counts update to reflect the subrange
      expect(screen.getByTestId('partitions-selected')).toHaveTextContent('150 Partitions');
    });
    await waitFor(() => {
      expect(screen.getByText('Missing (135)')).toBeVisible();
      expect(screen.getByText('Materialized (15)')).toBeVisible();
    });
    await waitFor(() => {
      // Verify that the items shown on the left update to reflect the subrange
      expect(screen.queryByText('2022-06-01-01:00')).toBeNull();
      expect(screen.queryByText('2022-11-28-20:00')).toBeVisible();
    });
  });

  it('should sync time range selection to the URL', async () => {
    await act(async () => {
      render(<SingleDimensionAssetPartitions assetKey={{path: ['single_dimension_time']}} />);
    });

    const partitionInput = await waitFor(async () => {
      return screen.getByTestId('dimension-range-input');
    });
    await userEvent.clear(partitionInput);
    await userEvent.type(partitionInput, '{[}2022-11-28-20:00...2022-12-05-01:00{]}');
    await userEvent.tab();

    await waitFor(() => {
      expect(screen.getByTestId('router-search')).toHaveTextContent(
        'default_range=%5B2022-11-28-20%3A00...2022-12-05-01%3A00%5D',
      );
    });
  });

  it('should support filtering by partition status and sync state to the URL', async () => {
    await act(async () => {
      render(<SingleDimensionAssetPartitions assetKey={{path: ['single_dimension_time']}} />);
    });
    await waitFor(() => {
      expect(screen.getByTestId('partitions-selected')).toHaveTextContent('6,000 Partitions');
    });

    const successCheck = screen.getByTestId(
      `partition-status-${AssetPartitionStatus.MATERIALIZED}-checkbox`,
    );
    await userEvent.click(successCheck);
    expect(screen.getByTestId('router-search')).toHaveTextContent(
      `status=${AssetPartitionStatus.FAILED}%2C${AssetPartitionStatus.MATERIALIZING}%2C${AssetPartitionStatus.MISSING}`,
    );
    expect(screen.getByTestId('partitions-selected')).toHaveTextContent('5,310 Partitions');

    const missingCheck = screen.getByTestId(
      `partition-status-${AssetPartitionStatus.MISSING}-checkbox`,
    );
    await userEvent.click(missingCheck);
    expect(screen.getByTestId('router-search')).toHaveTextContent(
      `status=${AssetPartitionStatus.FAILED}`,
    );
    expect(screen.getByTestId('partitions-selected')).toHaveTextContent('22 Partitions Selected');

    await userEvent.click(successCheck);
    expect(screen.getByTestId('router-search')).toHaveTextContent(
      `status=${AssetPartitionStatus.FAILED}%2C${AssetPartitionStatus.MATERIALIZED}`,
    );
    expect(screen.getByTestId('partitions-selected')).toHaveTextContent('712 Partitions Selected');

    // verify that filtering by state updates the left sidebar
    expect(screen.queryByText('2022-08-31-00:00')).toBeVisible();
  });

  it('should support reverse sorting individual dimensions', async () => {
    const Component = () => {
      const [params, setParams] = React.useState<AssetViewParams>({});
      return (
        <MemoryRouter>
          <MockedProvider mocks={[MultiDimensionTimeFirstPartitionHealthQuery]}>
            <AssetPartitions
              assetKey={{path: ['multi_dimension_time_first']}}
              params={params}
              setParams={setParams}
              paramsTimeWindowOnly={false}
              assetPartitionDimensions={['date', 'zstate']}
              dataRefreshHint={undefined}
            />
          </MockedProvider>
        </MemoryRouter>
      );
    };
    await act(async () => {
      render(<Component />);
    });

    await waitFor(() => {
      expect(screen.getByTestId('partitions-date')).toBeVisible();
      expect(screen.getByTestId('partitions-zstate')).toBeVisible();
    });

    await waitFor(() => {
      expect(
        getByTestId(
          screen.getByTestId('partitions-date'),
          'asset-partition-row-2023-02-05-index-0',
        ),
      ).toBeVisible();
      expect(
        getByTestId(screen.getByTestId('partitions-zstate'), 'asset-partition-row-TN-index-0'),
      ).toBeVisible();
    });

    await userEvent.click(screen.getByTestId('sort-0'));

    await waitFor(() => {
      expect(
        getByTestId(
          screen.getByTestId('partitions-date'),
          'asset-partition-row-2021-05-06-index-0',
        ),
      ).toBeVisible();
      expect(
        getByTestId(screen.getByTestId('partitions-zstate'), 'asset-partition-row-TN-index-0'),
      ).toBeVisible();
    });

    await userEvent.click(screen.getByTestId('sort-1'));
    await waitFor(() => {
      expect(
        getByTestId(screen.getByTestId('partitions-zstate'), 'asset-partition-row-WV-index-0'),
      ).toBeVisible();
    });
  });

  it('should set the focused partition when you click a list element', async () => {
    await act(async () => {
      render(<SingleDimensionAssetPartitions assetKey={{path: ['single_dimension_static']}} />);
    });
    await waitFor(async () => {
      const listItem = screen.getByText('NC');
      await userEvent.click(listItem);
    });
    await waitFor(async () => {
      expect(screen.getByTestId('focused-partition')).toHaveTextContent('NC');
    });
  });

  it('should not render a top bar with a partition input for statically partitioned assets', async () => {
    await act(async () => {
      render(<SingleDimensionAssetPartitions assetKey={{path: ['single_dimension_static']}} />);
    });
    await waitFor(() => {
      expect(screen.getByTestId('partitions-selected')).toHaveTextContent('11 Partitions Selected');
      expect(screen.queryByTestId('dimension-range-input')).toBeNull();
    });
  });
});
