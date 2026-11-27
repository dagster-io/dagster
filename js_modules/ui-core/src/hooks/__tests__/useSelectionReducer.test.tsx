import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {useSelectionReducer} from '../useSelectionReducer';

describe('useSelectionReducer', () => {
  const Test = ({ids, group = []}: {ids: string[]; group?: string[]}) => {
    const [{checkedIds}, {onToggleFactory, onToggleAll, onToggleMany}] = useSelectionReducer(ids);

    return (
      <div>
        <input
          type="checkbox"
          aria-label="check-all"
          checked={checkedIds.size === ids.length}
          onChange={(e) => onToggleAll(e.target.checked)}
        />
        <input
          type="checkbox"
          aria-label="check-group"
          checked={group.length > 0 && group.every((id) => checkedIds.has(id))}
          onChange={(e) => onToggleMany(group, e.target.checked)}
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

  it.each([
    {from: 9, to: 10, checkedIds: ['j', 'k']},
    {from: 10, to: 9, checkedIds: ['j', 'k']},
    {from: 2, to: 12, checkedIds: ['c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm']},
  ])('shift-click selects every row from $from to $to', async ({from, to, checkedIds}) => {
    const user = userEvent.setup();
    const ids = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm'];
    render(<Test ids={ids} />);

    await user.click(await screen.findByRole('checkbox', {name: `checkbox-${ids[from]}`}));
    await user.keyboard('[ShiftLeft>]');
    await user.click(await screen.findByRole('checkbox', {name: `checkbox-${ids[to]}`}));
    await user.keyboard('[/ShiftLeft]');

    const checkedBoxes = await screen.findAllByRole('checkbox', {checked: true});
    expect(checkedBoxes.map((checkbox) => checkbox.getAttribute('aria-label'))).toEqual(
      checkedIds.map((id) => `checkbox-${id}`),
    );
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

  it('toggles many items at once without affecting others', async () => {
    const user = userEvent.setup();
    render(<Test ids={['a', 'b', 'c', 'd']} group={['b', 'c']} />);
    const checkGroup = await screen.findByRole('checkbox', {name: /check-group/i});
    const checkA = await screen.findByRole('checkbox', {name: /checkbox-a/i});
    const checkB = await screen.findByRole('checkbox', {name: /checkbox-b/i});
    const checkC = await screen.findByRole('checkbox', {name: /checkbox-c/i});
    const checkD = await screen.findByRole('checkbox', {name: /checkbox-d/i});

    await user.click(checkA);
    await user.click(checkGroup);
    expect(checkA).toBeChecked();
    expect(checkB).toBeChecked();
    expect(checkC).toBeChecked();
    expect(checkD).not.toBeChecked();

    await user.click(checkGroup);
    expect(checkA).toBeChecked();
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
