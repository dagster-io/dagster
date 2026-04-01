import {fireEvent, render, screen} from '@testing-library/react';

import {ManualPositionHandle} from '../ManualPositionHandle';

describe('ManualPositionHandle', () => {
  it('renders a neutral drag affordance when no reset handler is provided', () => {
    render(<ManualPositionHandle onDragStart={() => {}} />);

    expect(screen.getByLabelText('Drag to reposition')).toBeVisible();
    expect(screen.queryByLabelText('Reset position')).not.toBeInTheDocument();
  });

  it('calls drag start and suppresses parent mouse/click handlers', () => {
    const onDragStart = jest.fn();
    const onParentClick = jest.fn();
    const onParentMouseDown = jest.fn();

    render(
      <div onClick={onParentClick} onMouseDown={onParentMouseDown}>
        <ManualPositionHandle onDragStart={onDragStart} />
      </div>,
    );

    const handle = screen.getByLabelText('Drag to reposition');
    fireEvent.mouseDown(handle);
    fireEvent.click(handle);

    expect(onDragStart).toHaveBeenCalledTimes(1);
    expect(onParentMouseDown).not.toHaveBeenCalled();
    expect(onParentClick).not.toHaveBeenCalled();
  });

  it('renders a separate reset action when a reset handler is provided', () => {
    const onDragStart = jest.fn();
    const onReset = jest.fn();

    render(
      <ManualPositionHandle
        onDragStart={onDragStart}
        onReset={onReset}
        isManuallyPositioned
      />,
    );

    expect(screen.getByLabelText('Drag to reposition')).toBeVisible();
    expect(screen.getByLabelText('Reset to auto-layout')).toBeVisible();
  });

  it('resets on click without triggering drag or parent click handlers', () => {
    const onReset = jest.fn();
    const onDragStart = jest.fn();
    const onParentClick = jest.fn();

    render(
      <div onClick={onParentClick}>
        <ManualPositionHandle onDragStart={onDragStart} onReset={onReset} isManuallyPositioned />
      </div>,
    );

    fireEvent.click(screen.getByLabelText('Reset to auto-layout'));

    expect(onReset).toHaveBeenCalledTimes(1);
    expect(onDragStart).not.toHaveBeenCalled();
    expect(onParentClick).not.toHaveBeenCalled();
  });
});
