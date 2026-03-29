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

  it('resets on double click when a reset handler is provided', () => {
    const onReset = jest.fn();
    const onParentDoubleClick = jest.fn();

    render(
      <div onDoubleClick={onParentDoubleClick}>
        <ManualPositionHandle onDragStart={() => {}} onReset={onReset} isManuallyPositioned />
      </div>,
    );

    fireEvent.doubleClick(screen.getByLabelText('Reset position'));

    expect(onReset).toHaveBeenCalledTimes(1);
    expect(onParentDoubleClick).not.toHaveBeenCalled();
  });
});
