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
});
