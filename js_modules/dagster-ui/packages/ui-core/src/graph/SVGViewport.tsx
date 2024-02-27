import {Box, Colors, Icon, Slider, Tooltip} from '@dagster-io/ui-components';
import animate from 'amator';
import * as React from 'react';
import styled from 'styled-components';

import {IBounds} from './common';
import {makeSVGPortable} from './makeSVGPortable';

export interface SVGViewportInteractor {
  onMouseDown(viewport: SVGViewport, event: React.MouseEvent<HTMLDivElement>): void;
  onWheel(viewport: SVGViewport, event: WheelEvent): void;
  render?(viewport: SVGViewport): React.ReactElement<any> | null;
}

interface SVGViewportProps {
  graphWidth: number;
  graphHeight: number;
  graphHasNoMinimumZoom?: boolean;
  interactor: SVGViewportInteractor;
  defaultZoom: 'zoom-to-fit' | 'zoom-to-fit-width';
  maxZoom: number;
  maxAutocenterZoom: number;
  additionalToolbarElements?: React.ReactNode;
  onClick?: (event: React.MouseEvent<HTMLDivElement>) => void;
  onDoubleClick?: (event: React.MouseEvent<HTMLDivElement>) => void;
  onArrowKeyDown?: (
    event: React.KeyboardEvent<HTMLDivElement>,
    dir: 'left' | 'up' | 'right' | 'down',
  ) => void;
  children: (
    state: SVGViewportState,
    bounds: {top: number; left: number; bottom: number; right: number},
  ) => React.ReactNode;
}

interface SVGViewportState {
  x: number;
  y: number;
  scale: number;
  minScale: number;
  isClickHeld: boolean;
  isExporting: boolean;
}

interface Point {
  x: number;
  y: number;
}

export const DETAIL_ZOOM = 0.75;
const DEFAULT_ZOOM = 0.75;
const DEFAULT_MAX_AUTOCENTER_ZOOM = 1;
const DEFAULT_MIN_ZOOM = 0.17;
export const DEFAULT_MAX_ZOOM = 1.2;

const BUTTON_INCREMENT = 0.05;

const PanAndZoomInteractor: SVGViewportInteractor = {
  onMouseDown(viewport: SVGViewport, event: React.MouseEvent<HTMLDivElement>) {
    if (viewport._animation) {
      viewport._animation.cancel();
    }

    if (!viewport.element.current) {
      return;
    }

    if (event.target instanceof HTMLElement && event.target.closest('#zoom-slider-container')) {
      return;
    }

    const start = viewport.getOffsetXY(event);
    if (!start) {
      return;
    }

    let lastX: number = start.x;
    let lastY: number = start.y;
    const travel = {x: 0, y: 0};

    const onMove = (e: MouseEvent) => {
      const offset = viewport.getOffsetXY(e);
      if (!offset) {
        return;
      }

      const delta = {x: offset.x - lastX, y: offset.y - lastY};
      viewport.setState({
        x: viewport.state.x + delta.x,
        y: viewport.state.y + delta.y,
      });
      travel.x += Math.abs(delta.x);
      travel.y += Math.abs(delta.y);
      lastX = offset.x;
      lastY = offset.y;
    };

    viewport.setState({isClickHeld: true});
    const onCancelClick = (e: MouseEvent) => {
      // If you press, drag, and release the mouse we don't want it to trigger a click
      // beneath your cursor. onClick's within the DAG should only fire if you did not
      // drag the mouse.
      if (Math.sqrt(travel.x + travel.y) > 5) {
        e.stopImmediatePropagation();
        e.preventDefault();
      }
    };
    const onUp = () => {
      viewport.setState({isClickHeld: false});
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      setTimeout(() => {
        document.removeEventListener('click', onCancelClick, {capture: true});
      });
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    document.addEventListener('click', onCancelClick, {capture: true});
  },

  onWheel(viewport: SVGViewport, event: WheelEvent) {
    const viewportEl = viewport.element.current;
    if (!viewportEl) {
      return;
    }

    const inZoomControl =
      event.target instanceof HTMLElement && event.target.closest('[data-zoom-control]');

    const cursorPosition = !inZoomControl
      ? viewport.getOffsetXY(event)
      : {x: viewportEl.clientWidth / 2, y: viewportEl.clientHeight / 2};
    if (!cursorPosition) {
      return;
    }

    // convert wheel event units to a better scroll speed. This is a bit subjective
    // but the defaults feel a bit too fast.
    const panSpeed = 0.7;

    // On trackpads, the browser converts "pinch to zoom" into a vertical scroll with the ctrl
    // key modifier set. In apps like Figma, the Cmd (meta) + scroll wheel zooms, and we want
    // that behavior as well.
    //
    // We scale the raw event delta for these two cases differently so that one full-trackpad
    // pinch-to-zoom will go from min to ~1.0 zoom, and so that the mouse wheel "ticks" are each
    // a small step.
    //
    if (event.metaKey || event.ctrlKey || inZoomControl) {
      const zoomSpeed =
        event.deltaMode === WheelEvent.DOM_DELTA_LINE
          ? 0.05 // Firefox cmd+wheel, numbers are in lines and not px
          : Math.abs(event.deltaY) > 30
          ? 0.002 // Chrome, Edge, Safari cmd+wheel, numbers get very large
          : 0.01; // trackpad;
      const targetScale = viewport.state.scale * (1 - event.deltaY * zoomSpeed);
      const scale = Math.max(viewport.getMinZoom(), Math.min(viewport.getMaxZoom(), targetScale));

      viewport.adjustZoomRelativeToScreenPoint(scale, cursorPosition);
    } else if (event.shiftKey && !event.deltaX) {
      viewport.shiftXY(event.deltaY * panSpeed, 0);
    } else {
      viewport.shiftXY(-event.deltaX * panSpeed, -event.deltaY * panSpeed);
    }
  },

  render(viewport: SVGViewport) {
    return (
      <ZoomSliderContainer
        id="zoom-slider-container"
        onClick={(e: React.MouseEvent) => {
          // Disallow click event from being handled by SVGViewport container, to avoid
          // zoom button/slider mouse events from being treated as "background" clicks
          // on the SVG display.
          e.stopPropagation();
        }}
      >
        <Box flex={{direction: 'column', alignItems: 'center'}}>
          <Tooltip content="Zoom in">
            <IconButton
              style={{borderBottomLeftRadius: 0, borderBottomRightRadius: 0}}
              onClick={() => {
                const x = viewport.element.current!.clientWidth / 2;
                const y = viewport.element.current!.clientHeight / 2;
                const scale = Math.min(
                  viewport.getMaxZoom(),
                  viewport.state.scale + BUTTON_INCREMENT,
                );
                const adjusted = Math.round((scale + Number.EPSILON) * 100) / 100;
                viewport.adjustZoomRelativeToScreenPoint(adjusted, {x, y});
              }}
            >
              <Icon name="zoom_in" />
            </IconButton>
          </Tooltip>
          <Box
            style={{width: 32, height: 140}}
            padding={{vertical: 12}}
            background={Colors.backgroundDefault()}
            data-zoom-control={true}
            flex={{alignItems: 'center', direction: 'column'}}
            border={{side: 'left-and-right', color: Colors.borderDefault()}}
          >
            <Slider
              vertical
              min={viewport.getMinZoom()}
              max={viewport.getMaxZoom()}
              stepSize={0.001}
              value={viewport.state.scale}
              labelRenderer={false}
              onChange={(scale: number) => {
                const x = viewport.element.current!.clientWidth / 2;
                const y = viewport.element.current!.clientHeight / 2;
                viewport.adjustZoomRelativeToScreenPoint(scale, {x, y});
              }}
            />
          </Box>
          <Tooltip content="Zoom out">
            <IconButton
              style={{borderTopLeftRadius: 0, borderTopRightRadius: 0}}
              onClick={() => {
                const x = viewport.element.current!.clientWidth / 2;
                const y = viewport.element.current!.clientHeight / 2;
                const scale = Math.max(
                  viewport.getMinZoom(),
                  viewport.state.scale - BUTTON_INCREMENT,
                );
                viewport.adjustZoomRelativeToScreenPoint(scale, {x, y});
              }}
            >
              <Icon name="zoom_out" />
            </IconButton>
          </Tooltip>
        </Box>
        <Box flex={{direction: 'column', alignItems: 'center', gap: 8}} margin={{top: 8}}>
          {viewport.props.additionalToolbarElements}
          <Box>
            <Tooltip content="Download as SVG">
              <IconButton onClick={() => viewport.onExportToSVG()}>
                <Icon name="download_for_offline" />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </ZoomSliderContainer>
    );
  },
};

const IconButton = styled.button`
  background: ${Colors.backgroundDefault()};
  border: 1px solid ${Colors.borderDefault()};
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  border-radius: 8px;
  transition: background 200ms ease-in-out;
}
  :hover {
    background-color: ${Colors.backgroundLightHover()};
  }

  :focus {
    outline: none;
  }

  :active {
    background-color: ${Colors.backgroundLight()};
  }
`;

const NoneInteractor: SVGViewportInteractor = {
  onMouseDown(_viewport: SVGViewport, event: React.MouseEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
  },

  onWheel() {
    return;
  },

  render() {
    return <span />;
  },
};

export class SVGViewport extends React.Component<SVGViewportProps, SVGViewportState> {
  static Interactors = {
    PanAndZoom: PanAndZoomInteractor,
    None: NoneInteractor,
  };

  static defaultProps = {
    maxZoom: DEFAULT_ZOOM,
    maxAutocenterZoom: DEFAULT_MAX_AUTOCENTER_ZOOM,
  };

  element: React.RefObject<HTMLDivElement> = React.createRef();
  panzoom: any;

  _animation: any = null;
  _lastWheelTime = 0;
  _lastWheelDir = 0;

  state = {
    x: 0,
    y: 0,
    scale: DETAIL_ZOOM,
    minScale: 0,
    isClickHeld: false,
    isExporting: false,
  };

  resizeObserver: any | undefined;

  componentDidMount() {
    this.autocenter();

    // The wheel event cannot be prevented via the `onWheel` handler.
    document.addEventListener('wheel', this.onWheel, {passive: false});

    // The op/asset graphs clip rendered nodes to the visible region, so changes to the
    // size of the viewport need to cause re-renders. Otherwise you expand the window
    // and see nothing in the newly visible areas.
    if (
      this.element.current &&
      this.element.current instanceof HTMLElement &&
      'ResizeObserver' in window
    ) {
      const RO = window['ResizeObserver'] as any;
      this.resizeObserver = new RO(() => {
        window.requestAnimationFrame(() => {
          this.forceUpdate();
        });
      });
      this.resizeObserver.observe(this.element.current);
    }
  }

  componentWillUnmount() {
    document.removeEventListener('wheel', this.onWheel);
    this.resizeObserver?.disconnect();
  }

  onWheel = (e: WheelEvent) => {
    const container = this.element.current;
    // If the wheel event occurs within our SVG container, prevent it from zooming
    // the document, and handle it with the interactor.
    if (container && e.target instanceof Node && container.contains(e.target)) {
      e.preventDefault();
      e.stopPropagation();
      this.props.interactor.onWheel(this, e);
    }
  };

  cancelAnimations() {
    if (this._animation) {
      this._animation.cancel();
    }
  }

  focus() {
    this.element.current?.focus();
  }

  scaleForSVGBounds(svgRegionWidth: number, svgRegionHeight: number) {
    const el = this.element.current;
    if (!el) {
      return 1;
    }
    const ownerRect = {width: el.clientWidth, height: el.clientHeight};

    const dw = ownerRect.width / svgRegionWidth;
    const dh = ownerRect.height / svgRegionHeight;
    return Math.min(dw, dh);
  }

  autocenter(animate = false, scale?: number) {
    const el = this.element.current!;
    const ownerRect = {width: el.clientWidth, height: el.clientHeight};

    const desiredScale =
      this.props.defaultZoom === 'zoom-to-fit-width'
        ? ownerRect.width / this.props.graphWidth
        : this.scaleForSVGBounds(this.props.graphWidth, this.props.graphHeight);

    const minScale = this.getMinZoom();
    const boundedScale =
      scale || Math.max(Math.min(desiredScale, this.props.maxAutocenterZoom), minScale);

    if (
      this.state.scale < boundedScale &&
      desiredScale !== boundedScale &&
      boundedScale === minScale
    ) {
      // If the user is zoomed out past where they're going to land, AND where they're going to land
      // is not a view of the entire DAG but instead a view of some zoomed section, autocentering is
      // undesirable and should do nothing.
      return;
    }
    const target = {
      x: -(this.props.graphWidth / 2) * boundedScale + ownerRect.width / 2,
      y: -(this.props.graphHeight / 2) * boundedScale + ownerRect.height / 2,
      scale: boundedScale,
    };

    if (animate) {
      this.smoothZoom(target);
    } else {
      this.setState(Object.assign(target, {minScale: boundedScale}));
    }
  }

  screenToSVGCoords({x, y}: Point): Point {
    const el = this.element.current!;
    const {width, height} = el.getBoundingClientRect();
    return {
      x: (-(this.state.x - width / 2) + x - width / 2) / this.state.scale,
      y: (-(this.state.y - height / 2) + y - height / 2) / this.state.scale,
    };
  }

  getOffsetXY(e: MouseEvent | React.MouseEvent): Point | null {
    const el = this.element.current;
    if (!el) {
      return null;
    }
    const ownerRect = el.getBoundingClientRect();
    return {x: e.clientX - ownerRect.left, y: e.clientY - ownerRect.top};
  }

  public shiftXY(dx: number, dy: number) {
    const {x, y, scale} = this.state;
    this.setState({x: x + dx, y: y + dy, scale});
  }

  public adjustZoomRelativeToScreenPoint(nextScale: number, point: Point) {
    const centerSVGCoord = this.screenToSVGCoords(point);
    const {scale} = this.state;
    let {x, y} = this.state;
    x = x + (centerSVGCoord.x * scale - centerSVGCoord.x * nextScale);
    y = y + (centerSVGCoord.y * scale - centerSVGCoord.y * nextScale);
    this.setState({x, y, scale: nextScale});
  }

  public zoomToSVGBox(box: IBounds, animate: boolean, newScale = this.state.scale) {
    this.zoomToSVGCoords(
      box.x + box.width / 2,
      box.y + box.height / 2,
      animate,
      newScale === this.getMinZoom() ? this.getMaxZoom() : newScale,
    );
  }

  public zoomToSVGCoords(x: number, y: number, animate: boolean, scale = this.state.scale) {
    const el = this.element.current!;
    const boundedScale = Math.max(Math.min(this.getMaxZoom(), scale), this.getMinZoom());

    const ownerRect = el.getBoundingClientRect();
    x = -x * boundedScale + ownerRect.width / 2;
    y = -y * boundedScale + ownerRect.height / 2;

    if (animate) {
      this.smoothZoom({x, y, scale: boundedScale});
    } else {
      this.setState({x, y, scale: boundedScale});
    }
  }

  public smoothZoom(to: {x: number; y: number; scale: number}) {
    const from = {scale: this.state.scale, x: this.state.x, y: this.state.y};

    if (this._animation) {
      this._animation.cancel();
    }

    this._animation = animate(from, to, {
      step: (v: any) => {
        this.setState({
          x: v.x,
          y: v.y,
          scale: v.scale,
        });
      },
      done: () => {
        this.setState(to);
        this._animation = null;
      },
    });
  }

  public getMinZoom() {
    if (this.props.graphHasNoMinimumZoom) {
      return Math.min(
        DEFAULT_MIN_ZOOM,
        this.scaleForSVGBounds(this.props.graphWidth, this.props.graphHeight),
      );
    }
    return DEFAULT_MIN_ZOOM;
  }

  public getMaxZoom() {
    return this.props.maxZoom;
  }

  public getViewport() {
    let viewport = {top: 0, left: 0, right: 0, bottom: 0};
    if (this.element.current) {
      const el = this.element.current!;
      const {width, height} = el.getBoundingClientRect();
      viewport = {
        left: -this.state.x / this.state.scale,
        top: -this.state.y / this.state.scale,
        right: (-this.state.x + width) / this.state.scale,
        bottom: (-this.state.y + height) / this.state.scale,
      };
    }
    return viewport;
  }

  onZoomAndCenter = (event: React.MouseEvent<HTMLDivElement>) => {
    const offsetXY = this.getOffsetXY(event);
    if (!offsetXY) {
      return;
    }
    const offset = this.screenToSVGCoords(offsetXY);
    const maxZoom = this.props.maxZoom || DEFAULT_ZOOM;

    if (Math.abs(maxZoom - this.state.scale) < 0.01) {
      this.zoomToSVGCoords(offset.x, offset.y, true, this.state.minScale);
    } else {
      this.zoomToSVGCoords(offset.x, offset.y, true, maxZoom);
    }
  };

  onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.target && (e.target as HTMLElement).nodeName === 'INPUT') {
      return;
    }

    const dir = (
      {
        ArrowLeft: 'left',
        ArrowUp: 'up',
        ArrowRight: 'right',
        ArrowDown: 'down',
      } as const
    )[e.code];
    if (!dir) {
      return;
    }

    e.preventDefault();
    e.stopPropagation();
    this.props.onArrowKeyDown?.(e, dir);
  };

  onDoubleClick = (event: React.MouseEvent<HTMLDivElement>) => {
    // Don't allow double-click events on the zoom slider to trigger this.
    if (event.target instanceof HTMLElement && event.target.closest('#zoom-slider-container')) {
      return;
    }
    this.props.onDoubleClick && this.props.onDoubleClick(event);
  };

  onExportToSVG = async () => {
    this.setState({isExporting: true});
  };

  render() {
    const {children, onClick, interactor} = this.props;
    const {x, y, scale, isClickHeld, isExporting} = this.state;
    const dotsize = Math.max(7, 22 * scale);

    return (
      <div
        ref={this.element}
        style={Object.assign({}, SVGViewportStyles, {
          backgroundPosition: `${x}px ${y}px`,
          backgroundSize: `${dotsize}px`,
          cursor: isClickHeld ? 'grabbing' : 'grab',
        })}
        data-svg-viewport="1"
        onMouseDown={(e) => interactor.onMouseDown(this, e)}
        onDoubleClick={this.onDoubleClick}
        onKeyDown={this.onKeyDown}
        onDragStart={(e) => e.preventDefault()}
        onClick={onClick}
        tabIndex={-1}
      >
        <div
          style={{
            transformOrigin: `top left`,
            transform: `matrix(${scale}, 0, 0, ${scale}, ${x}, ${y})`,
          }}
        >
          {children(
            this.state,
            isExporting
              ? {
                  top: 0,
                  left: 0,
                  right: this.props.graphWidth,
                  bottom: this.props.graphHeight,
                }
              : this.getViewport(),
          )}
          {isExporting ? (
            <SVGExporter
              element={this.element}
              onDone={() => this.setState({isExporting: false})}
            />
          ) : undefined}
        </div>
        {interactor.render && interactor.render(this)}
      </div>
    );
  }
}

/*
BG: Not using styled-components here because I need a `ref` to an actual DOM element.
Styled-component with a ref returns a React component we need to findDOMNode to use.
*/
const SVGViewportStyles: React.CSSProperties = {
  width: '100%',
  height: '100%',
  position: 'relative',
  overflow: 'hidden',
  userSelect: 'none',
  outline: 'none',
  background: `url("data:image/svg+xml;utf8,<svg width='30px' height='30px' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'><circle fill='${Colors.lineageDots()}' cx='5' cy='5' r='5' /></svg>") repeat`,
};

const ZoomSliderContainer = styled.div`
  position: absolute;
  bottom: 12px;
  right: 12px;
  width: 30px;
`;

const SVGExporter = ({
  element,
  onDone,
}: {
  element: React.RefObject<HTMLDivElement>;
  onDone: () => void;
}) => {
  React.useLayoutEffect(() => {
    const ready = async () => {
      // Find the rendered SVG node
      const svgOriginal = element.current?.querySelector('svg') as SVGElement;
      if (!svgOriginal) {
        onDone();
        return;
      }

      // Copy the node rendered by React, attach it and inline all the styles
      // (this mutates the DOM so it must be a copy of the element!)
      const svg = svgOriginal.cloneNode(true) as SVGElement;
      svgOriginal.parentElement?.appendChild(svg);
      await makeSVGPortable(svg);
      const text = new XMLSerializer().serializeToString(svg);
      svg.remove();

      // Trigger a file download
      const blob = new Blob([text], {type: 'image/svg+xml'});
      const a = document.createElement('a');
      a.setAttribute(
        'download',
        `${document.title.replace(/[: \/]/g, '_').replace(/__+/g, '_')}.svg`,
      );
      a.setAttribute('href', URL.createObjectURL(blob));
      a.click();

      onDone();
    };
    void ready();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <> </>;
};
