import {getByText, render, screen} from '@testing-library/react';
import React from 'react';

import {DynamicPartitionsRequestType, buildDynamicPartitionRequest} from '../../graphql/types';
import {DynamicPartitionRequests} from '../DynamicPartitionRequests';

describe('DynamicPartitionRequests', () => {
  it('renders an empty state when no requests are provided', () => {
    render(<DynamicPartitionRequests requests={[]} />);
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('renders a table with partition requests when requests are provided', () => {
    const requests = [
      buildDynamicPartitionRequest({
        partitionKeys: ['part1', 'part2'],
        partitionsDefName: 'def1',
        type: DynamicPartitionsRequestType.ADD_PARTITIONS,
      }),
      buildDynamicPartitionRequest({
        partitionKeys: ['part3'],
        partitionsDefName: 'def2',
        type: DynamicPartitionsRequestType.DELETE_PARTITIONS,
      }),
    ];

    render(<DynamicPartitionRequests requests={requests} />);

    expect(screen.getByRole('table')).toBeInTheDocument();
    const allRows = screen.getAllByRole('row');
    expect(allRows).toHaveLength(4); // 3 data rows + 1 header row

    // Verify header row content
    const headerRow = screen.getByRole('row', {
      name: /partition.*partition definition.*requested change/i,
    });
    expect(headerRow).toBeVisible();

    //First row
    expect(getByText(allRows[1], 'part1')).toBeVisible();
    expect(getByText(allRows[1], 'Add Partition')).toBeVisible();
    expect(getByText(allRows[1], 'def1')).toBeVisible();

    //Second row
    expect(getByText(allRows[2], 'part2')).toBeVisible();
    expect(getByText(allRows[2], 'Add Partition')).toBeVisible();
    expect(getByText(allRows[2], 'def1')).toBeVisible();

    //Third row
    expect(getByText(allRows[3], 'part3')).toBeVisible();
    expect(getByText(allRows[3], 'Delete Partition')).toBeVisible();
    expect(getByText(allRows[3], 'def2')).toBeVisible();
  });
});
