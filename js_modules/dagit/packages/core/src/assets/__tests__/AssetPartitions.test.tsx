import {MockedProvider} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent, {specialChars} from '@testing-library/user-event';
import React from 'react';
import {MemoryRouter, Route} from 'react-router-dom';

import {AssetKeyInput} from '../../graphql/types';
import {AssetPartitionListProps} from '../AssetPartitionList';
import {AssetPartitions} from '../AssetPartitions';
import {AssetViewParams} from '../AssetView';
import {
  SingleDimensionStaticPartitionHealthQuery,
  SingleDimensionTimePartitionHealthQuery,
} from '../__fixtures__/PartitionHealthSummary.mocks';

// This file must be mocked because useVirtualizer tries to create a ResizeObserver,
// and the component tree fails to mount. We still want to test whether certain partitions
// are shown, so we print the keys in a simple "list".
jest.mock('../AssetPartitionList', () => ({
  AssetPartitionList: (props: AssetPartitionListProps) => (
    <div>
      <div data-testid="focused-partition">{props.focusedDimensionKey}</div>
      {props.partitions.slice(0, 50).map((p) => (
        <div key={p} onClick={() => props.setFocusedDimensionKey?.(p)}>
          {p}
        </div>
      ))}
    </div>
  ),
}));

const SingleDimensionAssetPartitions: React.FC<{assetKey: AssetKeyInput}> = ({assetKey}) => {
  const [params, setParams] = React.useState<AssetViewParams>({});
  return (
    <MemoryRouter>
      <MockedProvider
        mocks={[SingleDimensionTimePartitionHealthQuery, SingleDimensionStaticPartitionHealthQuery]}
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
    await userEvent.type(partitionInput, specialChars.selectAll);
    await userEvent.type(partitionInput, specialChars.backspace);
    await userEvent.type(partitionInput, '[2022-11-28-20:00...2022-12-05-01:00]');
    await userEvent.tab();

    await waitFor(() => {
      // Verify that the counts update to reflect the subrange
      expect(screen.getByTestId('partitions-selected')).toHaveTextContent('150 Partitions');
    });
    await waitFor(() => {
      expect(screen.getByText('Missing (135)')).toBeVisible();
      expect(screen.getByText('Completed (15)')).toBeVisible();
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

    await waitFor(async () => {
      const partitionInput = screen.getByTestId('dimension-range-input');
      await userEvent.type(partitionInput, specialChars.selectAll);
      await userEvent.type(partitionInput, specialChars.backspace);
      await userEvent.type(partitionInput, '[2022-11-28-20:00...2022-12-05-01:00]', {delay: 1});
      await userEvent.tab();
    });

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

    const successCheck = screen.getByTestId('partition-state-success-checkbox');
    await userEvent.click(successCheck);
    expect(screen.getByTestId('router-search')).toHaveTextContent('states=failure%2Cmissing');
    expect(screen.getByTestId('partitions-selected')).toHaveTextContent('5,310 Partitions');

    const missingCheck = screen.getByTestId('partition-state-missing-checkbox');
    await userEvent.click(missingCheck);
    expect(screen.getByTestId('router-search')).toHaveTextContent('states=failure');
    expect(screen.getByTestId('partitions-selected')).toHaveTextContent('22 Partitions Selected');

    await userEvent.click(successCheck);
    expect(screen.getByTestId('router-search')).toHaveTextContent('states=failure%2Csuccess');
    expect(screen.getByTestId('partitions-selected')).toHaveTextContent('712 Partitions Selected');

    // verify that filtering by state updates the left sidebar
    expect(screen.queryByText('2022-08-31-00:00')).toBeVisible();
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
