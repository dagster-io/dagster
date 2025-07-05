import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {useSelectionReducer} from '../useSelectionReducer';

describe('useSelectionReducer', () => {
  const Test = ({ids}: {ids: string[]}) => {
    const [{checkedIds}, {onToggleFactory, onToggleAll}] = useSelectionReducer(ids);

    return (
      <div>
        <input
          type="checkbox"
          aria-label="check-all"
          checked={checkedIds.size === ids.length}
          onChange={(e) => onToggleAll(e.target.checked)}
        />
        {ids.map((id) => (
          <input
            key={id}
            type="checkbox"
            onChange={(e: React.FormEvent<HTMLInputElement>) => {
              if (e.target instanceof HTMLInputElement) {
                const onToggleChecked = onToggleFactory(id);
                const {checked} = e.target;
                const shiftKey =
                  e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
                onToggleChecked({checked, shiftKey});
              }
            }}
            aria-label={`checkbox-${id}`}
            checked={checkedIds.has(id)}
          />
        ))}
      </div>
    );
  };

  it('checks individual items', async () => {
    const user = userEvent.setup();
    render(<Test ids={['a', 'b', 'c', 'd']} />);
    const checkA = await screen.findByRole('checkbox', {name: /checkbox-a/i});
    expect(checkA).not.toBeChecked();
    await user.click(checkA);
    expect(checkA).toBeChecked();
    await user.click(checkA);
    expect(checkA).not.toBeChecked();
  });

  it('checks slices of items', async () => {
    const user = userEvent.setup();
    render(<Test ids={['a', 'b', 'c', 'd']} />);
    const checkA = await screen.findByRole('checkbox', {name: /checkbox-a/i});
    const checkB = await screen.findByRole('checkbox', {name: /checkbox-b/i});
    const checkC = await screen.findByRole('checkbox', {name: /checkbox-c/i});
    const checkD = await screen.findByRole('checkbox', {name: /checkbox-d/i});

    expect(checkA).not.toBeChecked();
    expect(checkB).not.toBeChecked();
    expect(checkC).not.toBeChecked();
    expect(checkD).not.toBeChecked();

    await user.click(checkA);
    expect(checkA).toBeChecked();
    await user.keyboard('[ShiftLeft>]');
    await user.click(checkC);

    expect(checkA).toBeChecked();
    expect(checkB).toBeChecked();
    expect(checkC).toBeChecked();
    expect(checkD).not.toBeChecked();

    await user.click(checkB);
    // Release key.
    await user.keyboard('[/ShiftLeft]');

    expect(checkA).toBeChecked();
    expect(checkB).not.toBeChecked();
    expect(checkC).not.toBeChecked();
    expect(checkD).not.toBeChecked();
  });

  it('allows toggle-all', async () => {
    const user = userEvent.setup();
    render(<Test ids={['a', 'b', 'c', 'd']} />);
    const checkAll = await screen.findByRole('checkbox', {name: /check-all/i});
    const checkA = await screen.findByRole('checkbox', {name: /checkbox-a/i});
    const checkB = await screen.findByRole('checkbox', {name: /checkbox-b/i});
    const checkC = await screen.findByRole('checkbox', {name: /checkbox-c/i});
    const checkD = await screen.findByRole('checkbox', {name: /checkbox-d/i});

    expect(checkA).not.toBeChecked();
    expect(checkB).not.toBeChecked();
    expect(checkC).not.toBeChecked();
    expect(checkD).not.toBeChecked();

    await user.click(checkAll);

    expect(checkA).toBeChecked();
    expect(checkB).toBeChecked();
    expect(checkC).toBeChecked();
    expect(checkD).toBeChecked();

    await user.click(checkAll);

    expect(checkA).not.toBeChecked();
    expect(checkB).not.toBeChecked();
    expect(checkC).not.toBeChecked();
    expect(checkD).not.toBeChecked();
  });

  it('allows updating allIds', async () => {
    const user = userEvent.setup();
    const {rerender} = render(<Test ids={['a', 'b', 'c', 'd']} />);

    const checkA = await screen.findByRole('checkbox', {name: /checkbox-a/i});
    const checkB = await screen.findByRole('checkbox', {name: /checkbox-b/i});
    const checkC = await screen.findByRole('checkbox', {name: /checkbox-c/i});
    const checkD = await screen.findByRole('checkbox', {name: /checkbox-d/i});

    await user.click(checkA);
    expect(checkA).toBeChecked();

    await user.keyboard('[ShiftLeft>]');
    await user.click(checkC);
    // Release key.
    await user.keyboard('[/ShiftLeft]');

    expect(checkA).toBeChecked();
    expect(checkB).toBeChecked();
    expect(checkC).toBeChecked();
    expect(checkD).not.toBeChecked();

    rerender(<Test ids={['a', 'b', 'c', 'd', 'e']} />);

    const checkE = await screen.findByRole('checkbox', {name: /checkbox-e/i});

    await user.click(checkE);
    expect(checkE).toBeChecked();
    await user.keyboard('[ShiftLeft>]');
    await user.click(checkD);

    // Release key.
    await user.keyboard('[/ShiftLeft]');

    expect(checkA).toBeChecked();
    expect(checkB).toBeChecked();
    expect(checkC).toBeChecked();
    expect(checkD).toBeChecked();
    expect(checkE).toBeChecked();

    // Now remove some of the original items.
    rerender(<Test ids={['c', 'd', 'e']} />);

    expect(checkC).toBeChecked();
    expect(checkD).toBeChecked();
    expect(checkE).toBeChecked();

    await user.click(checkE);
    expect(checkE).not.toBeChecked();
    await user.keyboard('[ShiftLeft>]');
    await user.click(checkD);

    // Release key.
    await user.keyboard('[/ShiftLeft]');

    expect(checkC).toBeChecked();
    expect(checkD).not.toBeChecked();
    expect(checkE).not.toBeChecked();
  });
});
