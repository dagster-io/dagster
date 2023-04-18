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

  it('checks individual items', () => {
    render(<Test ids={['a', 'b', 'c', 'd']} />);
    const checkA = screen.getByRole('checkbox', {name: /checkbox-a/i});
    expect(checkA).not.toBeChecked();
    userEvent.click(checkA);
    expect(checkA).toBeChecked();
    userEvent.click(checkA);
    expect(checkA).not.toBeChecked();
  });

  it('checks slices of items', () => {
    render(<Test ids={['a', 'b', 'c', 'd']} />);
    const checkA = screen.getByRole('checkbox', {name: /checkbox-a/i});
    const checkB = screen.getByRole('checkbox', {name: /checkbox-b/i});
    const checkC = screen.getByRole('checkbox', {name: /checkbox-c/i});
    const checkD = screen.getByRole('checkbox', {name: /checkbox-d/i});

    expect(checkA).not.toBeChecked();
    expect(checkB).not.toBeChecked();
    expect(checkC).not.toBeChecked();
    expect(checkD).not.toBeChecked();

    userEvent.click(checkA);
    expect(checkA).toBeChecked();
    userEvent.click(checkC, {shiftKey: true});

    expect(checkA).toBeChecked();
    expect(checkB).toBeChecked();
    expect(checkC).toBeChecked();
    expect(checkD).not.toBeChecked();

    userEvent.click(checkB, {shiftKey: true});
    expect(checkA).toBeChecked();
    expect(checkB).not.toBeChecked();
    expect(checkC).not.toBeChecked();
    expect(checkD).not.toBeChecked();
  });

  it('allows toggle-all', () => {
    render(<Test ids={['a', 'b', 'c', 'd']} />);
    const checkAll = screen.getByRole('checkbox', {name: /check-all/i});
    const checkA = screen.getByRole('checkbox', {name: /checkbox-a/i});
    const checkB = screen.getByRole('checkbox', {name: /checkbox-b/i});
    const checkC = screen.getByRole('checkbox', {name: /checkbox-c/i});
    const checkD = screen.getByRole('checkbox', {name: /checkbox-d/i});

    expect(checkA).not.toBeChecked();
    expect(checkB).not.toBeChecked();
    expect(checkC).not.toBeChecked();
    expect(checkD).not.toBeChecked();

    userEvent.click(checkAll);

    expect(checkA).toBeChecked();
    expect(checkB).toBeChecked();
    expect(checkC).toBeChecked();
    expect(checkD).toBeChecked();

    userEvent.click(checkAll);

    expect(checkA).not.toBeChecked();
    expect(checkB).not.toBeChecked();
    expect(checkC).not.toBeChecked();
    expect(checkD).not.toBeChecked();
  });
});
