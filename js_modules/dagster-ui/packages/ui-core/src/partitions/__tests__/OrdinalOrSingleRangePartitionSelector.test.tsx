import {render, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {TWO_DIMENSIONAL_ASSET_BOTH_STATIC} from '../../assets/__fixtures__/PartitionHealth.fixtures';
import {PartitionHealthQuery} from '../../assets/types/usePartitionHealthData.types';
import {
  PartitionDimensionSelection,
  buildPartitionHealthData,
} from '../../assets/usePartitionHealthData';
import {mockViewportClientRect, restoreViewportClientRect} from '../../testing/mocking';
import {OrdinalOrSingleRangePartitionSelector} from '../OrdinalOrSingleRangePartitionSelector';

const Wrapper = ({
  queryResult,
  initialSelection,
}: {
  queryResult: PartitionHealthQuery;
  initialSelection?: PartitionDimensionSelection | null;
}) => {
  const assetHealth = buildPartitionHealthData(queryResult, {path: ['asset']});
  const [selection, setSelection] = React.useState<PartitionDimensionSelection | null | undefined>(
    initialSelection,
  );
  return (
    <>
      <OrdinalOrSingleRangePartitionSelector
        dimension={assetHealth.dimensions[0]!}
        health={assetHealth}
        selection={selection}
        setSelection={setSelection}
      />
      <div data-testid="selection">
        {selection
          ? JSON.stringify({
              selectedKeys: selection.selectedKeys,
              selectedRanges: selection.selectedRanges,
            })
          : selection === null
          ? 'null'
          : selection === undefined
          ? 'undefined'
          : ''}
      </div>
    </>
  );
};
describe('OrdinalOrSingleRangePartitionSelector', () => {
  beforeAll(() => {
    mockViewportClientRect();
  });
  afterAll(() => {
    restoreViewportClientRect();
  });

  it('should populate with an existing value (selectedKeys)', async () => {
    const {baseElement, getByTitle} = render(
      <Wrapper
        queryResult={TWO_DIMENSIONAL_ASSET_BOTH_STATIC}
        initialSelection={{dimension: {} as any, selectedKeys: ['CA', 'MN'], selectedRanges: []}}
      />,
    );
    expect(baseElement.querySelector('[aria-selected=true]')?.textContent).toEqual('Single');
    expect(getByTitle('CA')).toBeVisible(); // tags are in the element
    expect(getByTitle('MN')).toBeVisible();
  });

  it('should populate with an existing value (null)', async () => {
    const {getByText, baseElement} = render(
      <Wrapper queryResult={TWO_DIMENSIONAL_ASSET_BOTH_STATIC} initialSelection={null} />,
    );
    expect(baseElement.querySelector('[aria-selected=true]')?.textContent).toEqual('All');
    expect(getByText('5 partitions')).toBeVisible();
  });

  it('should support All or Single entry for static partition dimensions', async () => {
    const {getByText, getByTestId, queryByText} = render(
      <Wrapper queryResult={TWO_DIMENSIONAL_ASSET_BOTH_STATIC} />,
    );
    expect(getByText('All')).toBeVisible();
    expect(getByText('Single')).toBeVisible();
    expect(queryByText('Range')).not.toBeInTheDocument();

    expect(getByTestId('selection').textContent).toEqual('undefined');

    const user = userEvent.setup();

    // Click All, verify the value changes to `null`
    await user.click(getByText('All'));
    await waitFor(() => {
      expect(getByTestId('selection').textContent).toEqual('null');
    });

    // Click Single, verify the value changes to an empty selection
    await user.click(getByText('Single'));
    await waitFor(() => {
      expect(getByTestId('selection').textContent).toEqual(
        '{"selectedKeys":[],"selectedRanges":[]}',
      );
    });

    // Click a few partitions, verify the values are added to the selection
    await user.click(getByText('Select a partition'));
    await user.click(getByTestId(`menu-item-CA`));
    await user.click(getByTestId(`menu-item-MN`));
    expect(getByTestId('selection').textContent).toEqual(
      '{"selectedKeys":["CA","MN"],"selectedRanges":[]}',
    );
  });
});
