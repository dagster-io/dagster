import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {createRef} from 'react';

import '@testing-library/jest-dom';
import {DEFAULT_MAX_ZOOM} from '../SVGConsts';
import {SVGViewport, SVGViewportProps, SVGViewportRef} from '../SVGViewport';

jest.mock('../SVGExporter', () => ({
  SVGExporter: () => <div data-testid="svg-exporter-component">SVG Exporter</div>,
}));

jest.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(() => ({
  width: 100,
  height: 100,
  top: 0,
  left: 0,
  right: 100,
  bottom: 100,
  x: 0,
  y: 0,
  toJSON: () => {},
}));

jest.mock('../SVGConsts', () => ({
  DEFAULT_MAX_ZOOM: 100,
  DEFAULT_MIN_ZOOM: 0,
  DEFAULT_ZOOM: 50,
  DEFAULT_MAX_AUTOCENTER_ZOOM: 50,
  DETAIL_ZOOM: 50,
}));

const DEFAULT_PROPS: SVGViewportProps = {
  graphWidth: 1000,
  graphHeight: 800,
  defaultZoom: 'zoom-to-fit',
  children: () => <div style={{width: 500, height: 500}}>Mock Graph</div>,
};

// jsdom (as of the version this repo pins) has no PointerEvent constructor at
// all, so `fireEvent.pointerDown` et al. can't fill in clientX/clientY/
// pointerId/pointerType the way a real browser would. Build the event by hand
// instead: a plain Event with those properties assigned is exactly what our
// native `addEventListener('pointerdown', ...)` handlers read.
function firePointerEvent(
  el: Element,
  type: 'pointerdown' | 'pointermove' | 'pointerup',
  init: {pointerId: number; pointerType: string; clientX: number; clientY: number},
) {
  const event = new Event(type, {bubbles: true, cancelable: true});
  Object.assign(event, init);
  act(() => {
    el.dispatchEvent(event);
  });
}

describe('SVGViewport', () => {
  it('renders without crashing', () => {
    render(<SVGViewport {...DEFAULT_PROPS} />);
    expect(screen.getByText('Mock Graph')).toBeInTheDocument();
  });

  it('focuses when focus() is called on the ref', () => {
    const ref = createRef<SVGViewportRef>();
    render(<SVGViewport {...DEFAULT_PROPS} ref={ref} />);
    act(() => {
      ref.current?.focus();
    });
    expect(document.activeElement).toEqual(screen.getByTestId('svg-viewport-container'));
  });

  it('calls onClick callback', async () => {
    const handleClick = jest.fn();
    render(<SVGViewport {...DEFAULT_PROPS} onClick={handleClick} />);
    const container = screen.getByTestId('svg-viewport-container');
    const user = userEvent.setup();
    await user.click(container);
    expect(handleClick).toHaveBeenCalled();
  });

  it('calls onDoubleClick callback if double-clicking away from slider', async () => {
    const handleDoubleClick = jest.fn();
    render(<SVGViewport {...DEFAULT_PROPS} onDoubleClick={handleDoubleClick} />);
    const container = screen.getByTestId('svg-viewport-container');
    const user = userEvent.setup();
    await user.dblClick(container);
    expect(handleDoubleClick).toHaveBeenCalled();
  });

  it('ignores double-clicks on zoom slider container', async () => {
    const handleDoubleClick = jest.fn();
    render(<SVGViewport {...DEFAULT_PROPS} onDoubleClick={handleDoubleClick} />);
    const sliderContainer = screen.getByTestId('zoom-slider-container');
    const user = userEvent.setup();
    await user.dblClick(sliderContainer);
    expect(handleDoubleClick).not.toHaveBeenCalled();
  });

  it('calls onArrowKeyDown on arrow keys when focused', async () => {
    const handleArrow = jest.fn();
    render(<SVGViewport {...DEFAULT_PROPS} onArrowKeyDown={handleArrow} />);
    const container = screen.getByTestId('svg-viewport-container');
    container.focus();
    const user = userEvent.setup();
    await user.keyboard('{ArrowLeft}');
    await user.keyboard('{ArrowUp}');
    await user.keyboard('{ArrowRight}');
    await user.keyboard('{ArrowDown}');
    expect(handleArrow).toHaveBeenCalledTimes(4);
  });

  it('clicking zoom in button updates the scale', async () => {
    const ref = createRef<SVGViewportRef>();
    render(<SVGViewport {...DEFAULT_PROPS} ref={ref} />);
    const zoomInButton = screen.getByTestId('zoom-in-button');
    const initialScale = ref.current?.getScale();
    const user = userEvent.setup();
    await user.click(zoomInButton);
    expect(ref.current?.getScale()).toBeGreaterThan(initialScale as number);
  });

  it('clicking zoom out button updates the scale', async () => {
    const ref = createRef<SVGViewportRef>();
    render(<SVGViewport {...DEFAULT_PROPS} ref={ref} />);
    const zoomOutButton = screen.getByTestId('zoom-out-button');
    const initialScale = ref.current?.getScale();
    const user = userEvent.setup();
    await user.click(zoomOutButton);
    expect(ref.current?.getScale()).toBeLessThan(initialScale as number);
  });

  it('restricts scale to the defined max zoom when zooming in', async () => {
    const ref = createRef<SVGViewportRef>();
    render(<SVGViewport {...DEFAULT_PROPS} ref={ref} />);
    const zoomInButton = screen.getByTestId('zoom-in-button');
    const user = userEvent.setup();
    for (let i = 0; i < 50; i++) {
      await user.click(zoomInButton);
    }
    expect(ref.current?.getScale()).toBeLessThanOrEqual(DEFAULT_MAX_ZOOM);
  });

  it('exports SVG on export button click', async () => {
    const ref = createRef<SVGViewportRef>();
    render(<SVGViewport {...DEFAULT_PROPS} ref={ref} />);
    const exportBtn = screen.getByTestId('export-svg-button');
    const user = userEvent.setup();
    await user.click(exportBtn);
    expect(screen.getByTestId('svg-exporter-component')).toBeInTheDocument();
  });

  it('calls cancelAnimations() without error', () => {
    const ref = createRef<SVGViewportRef>();
    render(<SVGViewport {...DEFAULT_PROPS} ref={ref} />);
    expect(() => ref.current?.cancelAnimations()).not.toThrow();
  });

  it('shifts position with shiftXY()', () => {
    const ref = createRef<SVGViewportRef>();
    render(<SVGViewport {...DEFAULT_PROPS} ref={ref} />);
    const initialX = ref.current?.getViewport().left;
    ref.current?.shiftXY(100, 50);
    expect(ref.current?.getViewport().left).toBeLessThan(initialX as number);
  });

  it('updates scale with adjustZoomRelativeToScreenPoint()', async () => {
    const ref = createRef<SVGViewportRef>();
    act(() => {
      render(<SVGViewport {...DEFAULT_PROPS} ref={ref} />);
    });
    const currentLeft = ref.current?.getViewport().left;
    const currentTop = ref.current?.getViewport().top;
    act(() => {
      ref.current?.adjustZoomRelativeToScreenPoint(0.5, {x: 100, y: 100});
    });
    await waitFor(() => {
      expect(ref.current?.getScale()).toEqual(0.5);
    });
    expect(ref.current?.getViewport().left).toBeGreaterThan(currentLeft as number);
    expect(ref.current?.getViewport().top).toBeGreaterThan(currentTop as number);
  });

  it('pans the viewport with a one-finger touch drag', async () => {
    const ref = createRef<SVGViewportRef>();
    act(() => {
      render(<SVGViewport {...DEFAULT_PROPS} ref={ref} />);
    });
    const container = screen.getByTestId('svg-viewport-container');
    const initialLeft = ref.current?.getViewport().left as number;
    const initialTop = ref.current?.getViewport().top as number;
    firePointerEvent(container, 'pointerdown', {
      pointerId: 1,
      pointerType: 'touch',
      clientX: 50,
      clientY: 50,
    });
    firePointerEvent(container, 'pointermove', {
      pointerId: 1,
      pointerType: 'touch',
      clientX: 80,
      clientY: 70,
    });
    firePointerEvent(container, 'pointerup', {
      pointerId: 1,
      pointerType: 'touch',
      clientX: 80,
      clientY: 70,
    });
    await waitFor(() => {
      // Dragging right/down moves the graph with the finger, so the visible
      // region moves left/up in graph coordinates.
      expect(ref.current?.getViewport().left).toBeLessThan(initialLeft);
      expect(ref.current?.getViewport().top).toBeLessThan(initialTop);
    });
  });

  it('does not pan on mouse pointer events (handled separately by onMouseDown)', async () => {
    const ref = createRef<SVGViewportRef>();
    act(() => {
      render(<SVGViewport {...DEFAULT_PROPS} ref={ref} />);
    });
    const container = screen.getByTestId('svg-viewport-container');
    const initialLeft = ref.current?.getViewport().left as number;
    firePointerEvent(container, 'pointerdown', {
      pointerId: 1,
      pointerType: 'mouse',
      clientX: 50,
      clientY: 50,
    });
    firePointerEvent(container, 'pointermove', {
      pointerId: 1,
      pointerType: 'mouse',
      clientX: 80,
      clientY: 70,
    });
    firePointerEvent(container, 'pointerup', {
      pointerId: 1,
      pointerType: 'mouse',
      clientX: 80,
      clientY: 70,
    });
    expect(ref.current?.getViewport().left).toEqual(initialLeft);
  });

  it('zooms the viewport with a two-finger pinch', async () => {
    const ref = createRef<SVGViewportRef>();
    act(() => {
      render(<SVGViewport {...DEFAULT_PROPS} ref={ref} />);
    });
    const container = screen.getByTestId('svg-viewport-container');
    const initialScale = ref.current?.getScale() as number;
    firePointerEvent(container, 'pointerdown', {
      pointerId: 1,
      pointerType: 'touch',
      clientX: 40,
      clientY: 50,
    });
    firePointerEvent(container, 'pointerdown', {
      pointerId: 2,
      pointerType: 'touch',
      clientX: 60,
      clientY: 50,
    });
    firePointerEvent(container, 'pointermove', {
      pointerId: 1,
      pointerType: 'touch',
      clientX: 20,
      clientY: 50,
    });
    firePointerEvent(container, 'pointermove', {
      pointerId: 2,
      pointerType: 'touch',
      clientX: 80,
      clientY: 50,
    });
    firePointerEvent(container, 'pointerup', {
      pointerId: 1,
      pointerType: 'touch',
      clientX: 20,
      clientY: 50,
    });
    firePointerEvent(container, 'pointerup', {
      pointerId: 2,
      pointerType: 'touch',
      clientX: 80,
      clientY: 50,
    });
    await waitFor(() => {
      expect(ref.current?.getScale()).toBeGreaterThan(initialScale);
    });
  });
});
