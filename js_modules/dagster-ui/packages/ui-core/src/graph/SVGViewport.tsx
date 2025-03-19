import {Box, Colors, Icon, Slider, Tooltip} from '@dagster-io/ui-components';
import animate from 'amator';
import throttle from 'lodash/throttle';
import React, {
  KeyboardEvent as ReactKeyboardEvent,
  MouseEvent as ReactMouseEvent,
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
} from 'react';
import styled from 'styled-components';

import {DEFAULT_MAX_AUTOCENTER_ZOOM, DEFAULT_MIN_ZOOM, DEFAULT_ZOOM} from './SVGConsts';
import {SVGExporter} from './SVGExporter';
import {SVGViewportProvider, useSVGViewport} from './SVGViewportContext';
import {IBounds} from './common';
import {testId} from '../testing/testId';

export interface SVGViewportProps {
  graphWidth: number;
  graphHeight: number;
  graphHasNoMinimumZoom?: boolean;
  defaultZoom: 'zoom-to-fit' | 'zoom-to-fit-width';
  maxZoom?: number;
  maxAutocenterZoom?: number;
  additionalToolbarElements?: React.ReactNode;
  onClick?: (event: ReactMouseEvent<HTMLDivElement>) => void;
  onDoubleClick?: (event: ReactMouseEvent<HTMLDivElement>) => void;
  onArrowKeyDown?: (
    event: ReactKeyboardEvent<HTMLDivElement>,
    dir: 'left' | 'up' | 'right' | 'down',
  ) => void;
  children: (
    state: SVGViewportState,
    bounds: {top: number; left: number; bottom: number; right: number},
  ) => React.ReactNode;
  style?: React.CSSProperties;
}

interface SVGViewportState {
  x: number;
  y: number;
  scale: number;
  minScale: number;
  isClickHeld: boolean;
  isExporting: boolean;
}

export interface Point {
  x: number;
  y: number;
}

/** The methods we expose on the imperative ref. */
export interface SVGViewportRef {
  /** Programmatically focus the viewport’s container div. */
  focus(): void;
  /** Cancel any active “smoothZoom” animation. */
  cancelAnimations(): void;
  /** Compute a scale factor to fully contain an SVG region of the given size. */
  scaleForSVGBounds(svgRegionWidth: number, svgRegionHeight: number): number;
  /** Zoom and center the entire graph in the viewport. */
  autocenter(animate?: boolean, forcedScale?: number): void;
  /** Convert a point in screen coords (eg. from a mouse event) to SVG coords. */
  screenToSVGCoords(point: Point): Point;
  /** Return the offset of a mouse event relative to the viewport’s top-left corner. */
  getOffsetXY(e: MouseEvent | ReactMouseEvent): Point | null;
  /** Shift the current x/y of the zoom transform by the provided delta. */
  shiftXY(dx: number, dy: number): void;
  /** Zoom around a particular screen point, e.g. the mouse cursor. */
  adjustZoomRelativeToScreenPoint(nextScale: number, point: Point): void;
  /** Zoom to a specific bounding box within the SVG. */
  zoomToSVGBox(box: IBounds, animate: boolean, newScale?: number, alignTop?: boolean): void;
  /** Zoom to a specific x,y coordinate (in SVG space). */
  zoomToSVGCoords(x: number, y: number, animate: boolean, scale?: number): void;
  /** Smoothly animate the zoom transform from the current to the provided target. */
  smoothZoom(to: {x: number; y: number; scale: number}): void;
  /** Return the current scale of the viewport. */
  getScale(): number;
  /** Return the minimum allowed zoom factor. */
  getMinZoom(): number;
  /** Return the maximum allowed zoom factor. */
  getMaxZoom(): number;
  /** Return the bounding box of the visible viewport, in SVG coords. */
  getViewport(): {top: number; left: number; right: number; bottom: number};
  /** Trigger the “export to SVG” download workflow. */
  onExportToSVG(): void;
}

const BUTTON_INCREMENT = 0.05;

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

export const SVGViewport = forwardRef<SVGViewportRef, SVGViewportProps>((props, ref) => (
  <SVGViewportProvider>
    <SVGViewportInner {...props} ref={ref} />
  </SVGViewportProvider>
));

const SVGViewportInner = forwardRef<SVGViewportRef, SVGViewportProps>(
  (
    {
      graphWidth,
      graphHeight,
      graphHasNoMinimumZoom,
      defaultZoom,
      maxZoom = DEFAULT_ZOOM,
      maxAutocenterZoom = DEFAULT_MAX_AUTOCENTER_ZOOM,
      additionalToolbarElements,
      onClick,
      onDoubleClick,
      onArrowKeyDown,
      children,
      style,
    },
    ref,
  ) => {
    const {viewportState, viewportStateRef, setViewportState, mergeViewportState} =
      useSVGViewport();

    const element = useRef<HTMLDivElement>(null);
    const animationRef = useRef<any>(null);
    const resizeObserverRef = useRef<any>(null);

    const cancelAnimations = useCallback(() => {
      if (animationRef.current) {
        animationRef.current.cancel();
        animationRef.current = null;
      }
    }, []);

    const getMinZoom = useCallback(() => {
      if (graphHasNoMinimumZoom) {
        return Math.min(DEFAULT_MIN_ZOOM, scaleForSVGBounds(graphWidth, graphHeight));
      }
      return DEFAULT_MIN_ZOOM;
    }, [graphWidth, graphHeight, graphHasNoMinimumZoom]);

    const getMaxZoom = useCallback(() => {
      return maxZoom;
    }, [maxZoom]);

    function scaleForSVGBounds(svgRegionWidth: number, svgRegionHeight: number): number {
      const el = element.current;
      if (!el) {
        return 1;
      }
      const {width, height} = el.getBoundingClientRect();
      const dw = width / svgRegionWidth;
      const dh = height / svgRegionHeight;
      return Math.min(dw, dh);
    }

    function autocenter(animate = false, forcedScale?: number) {
      const el = element.current;
      if (!el) {
        return;
      }

      const {width, height} = el.getBoundingClientRect();
      const desiredScale =
        defaultZoom === 'zoom-to-fit-width'
          ? width / graphWidth
          : scaleForSVGBounds(graphWidth, graphHeight);

      const minScale = getMinZoom();
      const boundedScale = forcedScale
        ? forcedScale
        : Math.max(Math.min(desiredScale, maxAutocenterZoom), minScale);

      if (
        viewportStateRef.current.scale < boundedScale &&
        desiredScale !== boundedScale &&
        boundedScale === minScale
      ) {
        // If the user is zoomed out past where they're going to land, AND where they're going to land
        // is not a view of the entire DAG but instead a view of some zoomed section, autocentering is
        // undesirable and should do nothing.
        return;
      }

      const target = {
        x: -(graphWidth / 2) * boundedScale + width / 2,
        y: -(graphHeight / 2) * boundedScale + height / 2,
        scale: boundedScale,
      };

      if (animate) {
        smoothZoom(target);
      } else {
        setViewportState((prev) => ({
          ...prev,
          ...target,
          minScale: boundedScale,
        }));
      }
    }

    const screenToSVGCoords = useCallback(
      ({x, y}: Point): Point => {
        const el = element.current;
        if (!el) {
          return {x: 0, y: 0};
        }
        const {width, height} = el.getBoundingClientRect();
        return {
          x:
            (-(viewportStateRef.current.x - width / 2) + x - width / 2) /
            viewportStateRef.current.scale,
          y:
            (-(viewportStateRef.current.y - height / 2) + y - height / 2) /
            viewportStateRef.current.scale,
        };
      },
      [viewportStateRef],
    );

    function getViewport() {
      let viewport = {top: 0, left: 0, right: 0, bottom: 0};
      const el = element.current;
      if (el) {
        const {width, height} = el.getBoundingClientRect();
        viewport = {
          left: -viewportStateRef.current.x / viewportStateRef.current.scale,
          top: -viewportStateRef.current.y / viewportStateRef.current.scale,
          right: (-viewportStateRef.current.x + width) / viewportStateRef.current.scale,
          bottom: (-viewportStateRef.current.y + height) / viewportStateRef.current.scale,
        };
      }
      return viewport;
    }

    const shiftXY = useCallback(
      (dx: number, dy: number) => {
        mergeViewportState((viewportState) => ({
          x: viewportState.x + dx,
          y: viewportState.y + dy,
        }));
      },
      [mergeViewportState],
    );

    const adjustZoomRelativeToScreenPoint = useCallback(
      (nextScale: number, point: Point) => {
        const centerSVGCoord = screenToSVGCoords(point);
        mergeViewportState((viewportState) => {
          const {scale} = viewportState;
          let {x, y} = viewportState;
          x = x + (centerSVGCoord.x * scale - centerSVGCoord.x * nextScale);
          y = y + (centerSVGCoord.y * scale - centerSVGCoord.y * nextScale);
          return {x, y, scale: nextScale};
        });
      },
      [mergeViewportState, screenToSVGCoords],
    );

    function zoomToSVGBox(
      box: IBounds,
      animate: boolean,
      newScale = viewportState.scale,
      alignTop = false,
    ) {
      // From the original class logic: toggle between min and max if scale == minZoom.
      const scaleToUse = newScale === getMinZoom() ? getMaxZoom() : newScale;
      const cx = box.x + box.width / 2;
      const cy = alignTop ? box.y : box.y + box.height / 2;
      zoomToSVGCoords(cx, cy, animate, scaleToUse);
    }

    function zoomToSVGCoords(x: number, y: number, animate: boolean, scale = viewportState.scale) {
      const el = element.current;
      if (!el) {
        return;
      }
      const boundedScale = Math.max(Math.min(getMaxZoom(), scale), getMinZoom());
      const {width, height} = el.getBoundingClientRect();

      const newX = -x * boundedScale + width / 2;
      const newY = -y * boundedScale + height / 2;

      if (animate) {
        smoothZoom({x: newX, y: newY, scale: boundedScale});
      } else {
        mergeViewportState({x: newX, y: newY, scale: boundedScale});
      }
    }

    function smoothZoom(to: {x: number; y: number; scale: number}) {
      const from = {
        scale: viewportState.scale,
        x: viewportState.x,
        y: viewportState.y,
      };
      cancelAnimations();

      animationRef.current = animate(from, to, {
        step: (v: any) => {
          setViewportState((prev) => ({
            ...prev,
            x: v.x,
            y: v.y,
            scale: v.scale,
          }));
        },
        done: () => {
          setViewportState((prev) => ({...prev, ...to}));
          animationRef.current = null;
        },
      });
    }

    // -- Mouse Handlers --

    const getOffsetXY = useCallback((e: MouseEvent | ReactMouseEvent): Point | null => {
      const el = element.current;
      if (!el) {
        return null;
      }
      const ownerRect = el.getBoundingClientRect();
      return {x: e.clientX - ownerRect.left, y: e.clientY - ownerRect.top};
    }, []);

    const onMouseDown = useCallback(
      (event: ReactMouseEvent<HTMLDivElement>) => {
        cancelAnimations();
        if (!element.current) {
          return;
        }
        // Ignore clicks on zoom slider
        if (event.target instanceof HTMLElement && event.target.closest('#zoom-slider-container')) {
          return;
        }

        const start = getOffsetXY(event);
        if (!start) {
          return;
        }

        let lastX = start.x;
        let lastY = start.y;
        const travel = {x: 0, y: 0};

        const onMove = throttle((e: MouseEvent) => {
          const offset = getOffsetXY(e);
          if (!offset) {
            return;
          }
          const delta = {x: offset.x - lastX, y: offset.y - lastY};
          setViewportState((prev) => ({
            ...prev,
            x: prev.x + delta.x,
            y: prev.y + delta.y,
          }));
          travel.x += Math.abs(delta.x);
          travel.y += Math.abs(delta.y);
          lastX = offset.x;
          lastY = offset.y;
        }, 1000 / 60);

        mergeViewportState({isClickHeld: true});

        const onCancelClick = (e: MouseEvent) => {
          if (Math.sqrt(travel.x + travel.y) > 5) {
            e.stopImmediatePropagation();
            e.preventDefault();
          }
        };

        const onUp = () => {
          mergeViewportState({isClickHeld: false});
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
      [cancelAnimations, getOffsetXY, mergeViewportState, setViewportState],
    );

    const onWheel = useMemo(
      () =>
        throttle((event: WheelEvent) => {
          const viewportEl = element.current;
          if (!viewportEl) {
            return;
          }
          const inZoomControl =
            event.target instanceof HTMLElement && event.target.closest('[data-zoom-control]');

          // Use cursor location unless in the zoom controls
          const cursorPosition = !inZoomControl
            ? getOffsetXY(event)
            : {
                x: viewportEl.clientWidth / 2,
                y: viewportEl.clientHeight / 2,
              };

          if (!cursorPosition) {
            return;
          }

          const panSpeed = 0.7;
          const {scale} = viewportStateRef.current;

          if (event.metaKey || event.ctrlKey || inZoomControl) {
            const zoomSpeed =
              event.deltaMode === WheelEvent.DOM_DELTA_LINE
                ? 0.05
                : Math.abs(event.deltaY) > 30
                  ? 0.002
                  : 0.01;
            const targetScale = scale * (1 - event.deltaY * zoomSpeed);
            const clamped = Math.max(getMinZoom(), Math.min(getMaxZoom(), targetScale));
            adjustZoomRelativeToScreenPoint(clamped, cursorPosition);
          } else if (event.shiftKey && !event.deltaX) {
            // shift + scroll => horizontal
            shiftXY(event.deltaY * panSpeed, 0);
          } else {
            // normal vertical / horizontal scrolling
            shiftXY(-event.deltaX * panSpeed, -event.deltaY * panSpeed);
          }
        }, 1000 / 60),
      [
        getOffsetXY,
        viewportStateRef,
        getMinZoom,
        getMaxZoom,
        adjustZoomRelativeToScreenPoint,
        shiftXY,
      ],
    );

    const handleKeyDown = useCallback(
      (e: ReactKeyboardEvent<HTMLDivElement>) => {
        // If typing in an input, ignore
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
        onArrowKeyDown?.(e, dir);
      },
      [onArrowKeyDown],
    );

    const handleDoubleClick = useCallback(
      (e: ReactMouseEvent<HTMLDivElement>) => {
        // Do not trigger if the user double-clicks on the zoom slider
        if (e.target instanceof HTMLElement && e.target.closest('#zoom-slider-container')) {
          return;
        }
        onDoubleClick?.(e);
      },
      [onDoubleClick],
    );

    const onExportToSVG = useCallback(() => {
      mergeViewportState({isExporting: true});
    }, [mergeViewportState]);

    useEffect(() => {
      // On mount, auto-center once
      autocenter(false);

      function onDocumentWheel(e: WheelEvent) {
        const container = element.current;
        if (container && e.target instanceof Node && container.contains(e.target)) {
          e.preventDefault();
          e.stopPropagation();
          onWheel(e);
        }
      }

      document.addEventListener('wheel', onDocumentWheel, {passive: false});

      // Observe resizing
      if (element.current && 'ResizeObserver' in window) {
        const RO = (window as any)['ResizeObserver'];
        resizeObserverRef.current = new RO(() => {
          window.requestAnimationFrame(() => {
            // Force a re-render so children can update if they rely on the size
            setViewportState((prev) => ({...prev}));
          });
        });
        resizeObserverRef.current.observe(element.current);
      }

      return () => {
        document.removeEventListener('wheel', onDocumentWheel);
        if (resizeObserverRef.current) {
          resizeObserverRef.current.disconnect();
        }
      };
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const {x, y, scale, isClickHeld, isExporting} = viewportState;
    const dotsize = Math.max(7, 22 * scale);

    const focusViewport = useCallback(() => {
      element.current?.focus();
    }, []);

    const getScale = useCallback(() => scale, [scale]);

    useImperativeHandle(ref, () => ({
      focus: focusViewport,
      cancelAnimations,
      scaleForSVGBounds,
      autocenter,
      screenToSVGCoords,
      getOffsetXY,
      shiftXY,
      adjustZoomRelativeToScreenPoint,
      zoomToSVGBox,
      zoomToSVGCoords,
      smoothZoom,
      getMinZoom,
      getMaxZoom,
      getViewport,
      onExportToSVG,
      getScale,
    }));

    return (
      <div
        ref={element}
        style={{
          ...SVGViewportStyles,
          ...style,
          backgroundPosition: `${x}px ${y}px`,
          backgroundSize: `${dotsize}px`,
          cursor: isClickHeld ? 'grabbing' : 'grab',
        }}
        data-svg-viewport="1"
        onMouseDown={onMouseDown}
        onDoubleClick={handleDoubleClick}
        onKeyDown={handleKeyDown}
        onDragStart={(e) => e.preventDefault()}
        onClick={onClick}
        tabIndex={-1}
        data-testid={testId('svg-viewport-container')}
      >
        <div
          style={{
            transformOrigin: 'top left',
            transform: `matrix(${scale}, 0, 0, ${scale}, ${x}, ${y})`,
          }}
        >
          {children(
            viewportState,
            isExporting
              ? {
                  top: 0,
                  left: 0,
                  right: graphWidth,
                  bottom: graphHeight,
                }
              : getViewport(),
          )}
          {isExporting && (
            <SVGExporter
              element={element}
              onDone={() => mergeViewportState({isExporting: false})}
            />
          )}
        </div>
        <ZoomSliderContainer
          id="zoom-slider-container"
          data-testid={testId('zoom-slider-container')}
          onClick={(e: ReactMouseEvent) => {
            // Disallow click from hitting parent
            e.stopPropagation();
          }}
          onDoubleClick={(e: ReactMouseEvent) => {
            // Disallow double-click from hitting parent
            e.stopPropagation();
          }}
        >
          <Box flex={{direction: 'column', alignItems: 'center'}}>
            <Tooltip content="Zoom in">
              <IconButton
                style={{borderBottomLeftRadius: 0, borderBottomRightRadius: 0}}
                onClick={() => {
                  const el = element.current;
                  if (!el) {
                    return;
                  }
                  const xMid = el.clientWidth / 2;
                  const yMid = el.clientHeight / 2;
                  const newScale = Math.min(getMaxZoom(), scale + BUTTON_INCREMENT);
                  const adjusted = Math.round((newScale + Number.EPSILON) * 100) / 100;
                  adjustZoomRelativeToScreenPoint(adjusted, {x: xMid, y: yMid});
                }}
                data-testid={testId('zoom-in-button')}
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
              data-testid={testId('zoom-slider')}
            >
              <Slider
                vertical
                min={getMinZoom()}
                max={getMaxZoom()}
                stepSize={0.001}
                value={scale}
                labelRenderer={false}
                onChange={(next: number) => {
                  const el = element.current;
                  if (!el) {
                    return;
                  }
                  const xMid = el.clientWidth / 2;
                  const yMid = el.clientHeight / 2;
                  adjustZoomRelativeToScreenPoint(next, {x: xMid, y: yMid});
                }}
              />
            </Box>
            <Tooltip content="Zoom out">
              <IconButton
                style={{borderTopLeftRadius: 0, borderTopRightRadius: 0}}
                onClick={() => {
                  const el = element.current;
                  if (!el) {
                    return;
                  }
                  const xMid = el.clientWidth / 2;
                  const yMid = el.clientHeight / 2;
                  const newScale = Math.max(getMinZoom(), scale - BUTTON_INCREMENT);
                  adjustZoomRelativeToScreenPoint(newScale, {x: xMid, y: yMid});
                }}
                data-testid={testId('zoom-out-button')}
              >
                <Icon name="zoom_out" />
              </IconButton>
            </Tooltip>
          </Box>
          <Box flex={{direction: 'column', alignItems: 'center', gap: 8}} margin={{top: 8}}>
            {additionalToolbarElements}
            <Box>
              <Tooltip content="Download as SVG">
                <IconButton onClick={onExportToSVG} data-testid={testId('export-svg-button')}>
                  <Icon name="download_for_offline" />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </ZoomSliderContainer>
      </div>
    );
  },
);
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
  background: `url("data:image/svg+xml;utf8,<svg width='30px' height='30px' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'><circle fill='rgba(103, 116, 138, 0.20)' cx='5' cy='5' r='5' /></svg>") repeat`,
};

const ZoomSliderContainer = styled.div`
  position: absolute;
  bottom: 12px;
  right: 12px;
  width: 30px;
`;
