import {render, waitFor, screen} from '@testing-library/react';
import React from 'react';

import {usePartitionKeyInParams} from '../usePartitionKeyInParams';

describe('usePartitionKeyInParams', () => {
  it('should parse and set a one-dimensional partition key', async () => {
    const HookUse: React.FC = () => {
      const setParams = jest.fn();
      const [focusedDimensionKeys, setFocusedDimensionKey] = usePartitionKeyInParams({
        params: {partition: 'VA'},
        setParams,
        dimensionCount: 1,
        defaultKeyInDimension: () => 'TN',
      });

      expect(focusedDimensionKeys).toEqual(['VA']);
      setFocusedDimensionKey(0, 'CA');
      expect(setParams).toHaveBeenCalledWith({partition: 'CA'});
      return <span>Done</span>;
    };

    render(<HookUse />);
    await waitFor(() => expect(screen.getByText('Done')).toBeVisible());
  });

  it('should default to no value for a one-dimensional partition key', async () => {
    const HookUse: React.FC = () => {
      const [focusedDimensionKeys] = usePartitionKeyInParams({
        params: {},
        setParams: jest.fn(),
        dimensionCount: 1,
        defaultKeyInDimension: () => 'TN',
      });
      expect(focusedDimensionKeys).toEqual([]);
      return <span>Done</span>;
    };

    render(<HookUse />);
    await waitFor(() => expect(screen.getByText('Done')).toBeVisible());
  });

  it('should parse and set a two-dimensional partition key', async () => {
    const HookUse: React.FC = () => {
      const setParams = jest.fn();
      const [focusedDimensionKeys, setFocusedDimensionKey] = usePartitionKeyInParams({
        params: {partition: '2022-05-01|VA'},
        setParams,
        dimensionCount: 2,
        defaultKeyInDimension: (idx: number) => (idx === 0 ? '2022-01-01' : 'TN'),
      });

      expect(focusedDimensionKeys).toEqual(['2022-05-01', 'VA']);

      // Note: both tests run from the params.partition initial state above

      // Changing the dimension 1 value clears the dimension 2 value
      setFocusedDimensionKey(0, '2022-05-02');
      expect(setParams).toHaveBeenCalledWith({partition: '2022-05-02'});

      // Changing the dimension 2 value does not change dimension 1 value
      setFocusedDimensionKey(1, 'CA');
      expect(setParams).toHaveBeenCalledWith({partition: '2022-05-01|CA'});
      return <span>Done</span>;
    };

    render(<HookUse />);
    await waitFor(() => expect(screen.getByText('Done')).toBeVisible());
  });

  it('should allow a partial selection of just the first partition key', async () => {
    const HookUse: React.FC = () => {
      const setParams = jest.fn();
      const [, setFocusedDimensionKey] = usePartitionKeyInParams({
        params: {partition: ''},
        setParams,
        dimensionCount: 2,
        defaultKeyInDimension: (idx: number) => (idx === 0 ? '2022-01-01' : 'TN'),
      });

      setFocusedDimensionKey(0, '2022-05-02');
      expect(setParams).toHaveBeenCalledWith({partition: '2022-05-02'});
      return <span>Done</span>;
    };

    render(<HookUse />);
    await waitFor(() => expect(screen.getByText('Done')).toBeVisible());
  });

  it('should default to no values for a two-dimensional partition key', async () => {
    const HookUse: React.FC = () => {
      const [focusedDimensionKeys] = usePartitionKeyInParams({
        params: {},
        setParams: jest.fn(),
        dimensionCount: 2,
        defaultKeyInDimension: (idx: number) => (idx === 0 ? '2022-01-01' : 'TN'),
      });

      expect(focusedDimensionKeys).toEqual([]);
      return <span>Done</span>;
    };

    render(<HookUse />);
    await waitFor(() => expect(screen.getByText('Done')).toBeVisible());
  });

  it('should default to the 1st key of dimension 1 if dimension 2 is selected first', async () => {
    const HookUse: React.FC = () => {
      const setParams = jest.fn();
      const [focusedDimensionKeys, setFocusedDimensionKey] = usePartitionKeyInParams({
        params: {},
        setParams,
        dimensionCount: 2,
        defaultKeyInDimension: (idx: number) => (idx === 0 ? '2022-01-01' : 'TN'),
      });

      expect(focusedDimensionKeys).toEqual([]);
      setFocusedDimensionKey(1, 'CA');
      expect(setParams).toHaveBeenCalledWith({partition: '2022-01-01|CA'});
      return <span>Done</span>;
    };

    render(<HookUse />);
    await waitFor(() => expect(screen.getByText('Done')).toBeVisible());
  });
});
