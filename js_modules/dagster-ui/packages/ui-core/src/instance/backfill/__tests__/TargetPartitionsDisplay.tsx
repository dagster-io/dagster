import {render} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

import {buildAssetBackfillTargetPartitions, buildPartitionKeyRange} from '../../../graphql/types';
import {TargetPartitionsDisplay} from '../TargetPartitionsDisplay';

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../../graph/asyncGraphLayout', () => ({}));
jest.mock('../../../app/QueryRefresh', () => {
  return {
    useQueryRefreshAtInterval: jest.fn(),
    QueryRefreshCountdown: jest.fn(() => <div />),
  };
});

describe('TargetPartitionsDisplay', () => {
  it('renders the targeted partitions when rootAssetTargetedPartitions is provided and length <= 3', async () => {
    const {getByText} = render(
      <TargetPartitionsDisplay
        targetPartitionCount={3}
        targetPartitions={buildAssetBackfillTargetPartitions({
          partitionKeys: ['1', '2', '3'],
          ranges: null,
        })}
      />,
    );

    expect(getByText('1')).toBeInTheDocument();
    expect(getByText('2')).toBeInTheDocument();
    expect(getByText('3')).toBeInTheDocument();
  });

  it('renders the targeted partitions in a dialog when rootAssetTargetedPartitions is provided and length > 3', async () => {
    const {getByText} = render(
      <TargetPartitionsDisplay
        targetPartitionCount={4}
        targetPartitions={buildAssetBackfillTargetPartitions({
          partitionKeys: ['1', '2', '3', '4'],
          ranges: null,
        })}
      />,
    );

    await userEvent.click(getByText('4 partitions'));

    expect(getByText('1')).toBeInTheDocument();
    expect(getByText('2')).toBeInTheDocument();
    expect(getByText('3')).toBeInTheDocument();
    expect(getByText('4')).toBeInTheDocument();
  });

  it('renders the single targeted range when rootAssetTargetedRanges is provided and length === 1', async () => {
    const {getByText} = render(
      <TargetPartitionsDisplay
        targetPartitionCount={1}
        targetPartitions={buildAssetBackfillTargetPartitions({
          partitionKeys: null,
          ranges: [buildPartitionKeyRange({start: '1', end: '2'})],
        })}
      />,
    );

    expect(getByText('1...2')).toBeInTheDocument();
  });

  it('renders the targeted ranges in a dialog when rootAssetTargetedRanges is provided and length > 1', async () => {
    const {getByText} = render(
      <TargetPartitionsDisplay
        targetPartitionCount={2}
        targetPartitions={buildAssetBackfillTargetPartitions({
          partitionKeys: null,
          ranges: [
            buildPartitionKeyRange({start: '1', end: '2'}),
            buildPartitionKeyRange({start: '3', end: '4'}),
          ],
        })}
      />,
    );

    await userEvent.click(getByText('2 partitions'));

    expect(getByText('1...2')).toBeInTheDocument();
    expect(getByText('3...4')).toBeInTheDocument();
  });

  it('renders the targetPartitionCount when neither rootAssetTargetedPartitions nor rootAssetTargetedRanges are provided', async () => {
    const {getByText} = render(<TargetPartitionsDisplay targetPartitionCount={2} />);

    expect(getByText('2 partitions')).toBeInTheDocument();
  });
});
