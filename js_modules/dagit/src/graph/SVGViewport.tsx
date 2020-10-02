import {Colors, Icon, Slider} from '@blueprintjs/core';
import animate from 'amator';
import * as React from 'react';
import styled from 'styled-components';

export interface SVGViewportInteractor {
  onMouseDown(viewport: SVGViewport, event: React.MouseEvent<HTMLDivElement>): void;
  onWheel(viewport: SVGViewport, event: React.MouseEvent<HTMLDivElement>): void;
  render?(viewport: SVGViewport): React.ReactElement<any> | null;
}

interface SVGViewportProps {
  graphWidth: number;
  graphHeight: number;
  backgroundColor?: string;
  interactor: SVGViewportInteractor;
  onDoubleClick: (event: React.MouseEvent<HTMLDivElement>) => void;
  onKeyDown: (event: React.KeyboardEvent<HTMLDivElement>) => void;
  children: (state: SVGViewportState) => React.ReactNode;
}

interface SVGViewportState {
  x: number;
  y: number;
  scale: number;
  minScale: number;
}

interface Point {
  x: number;
  y: number;
}

export const DETAIL_ZOOM = 0.75;
export const MAX_AUTOCENTER_ZOOM = 0.39;
export const MIN_AUTOCENTER_ZOOM = 0.15;
export const MIN_ZOOM = 0.015;

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
    let lastX: number = start.x;
    let lastY: number = start.y;

    const onMove = (e: MouseEvent) => {
      const offset = viewport.getOffsetXY(e);
      const delta = {x: offset.x - lastX, y: offset.y - lastY};
      viewport.setState({
        x: viewport.state.x + delta.x,
        y: viewport.state.y + delta.y,
      });
      lastX = offset.x;
      lastY = offset.y;
    };

    const onUp = () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    event.stopPropagation();
  },

  onWheel(viewport: SVGViewport, event: React.WheelEvent<HTMLDivElement>) {
    const cursorPosition = viewport.getOffsetXY(event);
    const targetScale = viewport.state.scale * (1 - event.deltaY * 0.0025);
    const scale = Math.max(MIN_ZOOM, Math.min(DETAIL_ZOOM, targetScale));
    viewport.adjustZoomRelativeToScreenPoint(scale, cursorPosition);
  },

  render(viewport: SVGViewport) {
    return (
      <ZoomSliderContainer id="zoom-slider-container">
        <Icon
          iconSize={17}
          icon="zoom-in"
          style={{color: Colors.LIGHT_GRAY1, marginBottom: 12}}
          onClick={() => {
            const x = viewport.element.current!.clientWidth / 2;
            const y = viewport.element.current!.clientHeight / 2;
            viewport.adjustZoomRelativeToScreenPoint(DETAIL_ZOOM, {x, y});
          }}
        />
        <Slider
          vertical
          min={MIN_ZOOM}
          max={DETAIL_ZOOM}
          stepSize={0.001}
          value={viewport.state.scale}
          labelRenderer={false}
          onChange={(scale: number) => {
            const x = viewport.element.current!.clientWidth / 2;
            const y = viewport.element.current!.clientHeight / 2;
            viewport.adjustZoomRelativeToScreenPoint(scale, {x, y});
          }}
        />
        <Icon
          iconSize={17}
          icon="zoom-out"
          style={{color: Colors.LIGHT_GRAY1, marginTop: 12}}
          onClick={() => {
            const x = viewport.element.current!.clientWidth / 2;
            const y = viewport.element.current!.clientHeight / 2;
            viewport.adjustZoomRelativeToScreenPoint(MIN_ZOOM, {x, y});
          }}
        />
      </ZoomSliderContainer>
    );
  },
};

const NoneInteractor: SVGViewportInteractor = {
  onMouseDown(viewport: SVGViewport, event: React.MouseEvent<HTMLDivElement>) {
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
  };

  componentDidMount() {
    this.autocenter();
  }

  cancelAnimations() {
    if (this._animation) {
      this._animation.cancel();
    }
  }

  autocenter(animate = false) {
    const el = this.element.current!;
    const ownerRect = {width: el.clientWidth, height: el.clientHeight};

    const dw = ownerRect.width / this.props.graphWidth;
    const dh = ownerRect.height / this.props.graphHeight;
    const desiredScale = Math.min(dw, dh);
    const boundedScale = Math.max(Math.min(desiredScale, MAX_AUTOCENTER_ZOOM), MIN_AUTOCENTER_ZOOM);

    if (
      this.state.scale < boundedScale &&
      desiredScale !== boundedScale &&
      boundedScale === MIN_AUTOCENTER_ZOOM
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

  getOffsetXY(e: MouseEvent | React.MouseEvent): Point {
    const el = this.element.current!;
    const ownerRect = el.getBoundingClientRect();
    return {x: e.clientX - ownerRect.left, y: e.clientY - ownerRect.top};
  }

  public adjustZoomRelativeToScreenPoint(nextScale: number, point: Point) {
    const centerSVGCoord = this.screenToSVGCoords(point);
    const {scale} = this.state;
    let {x, y} = this.state;
    x = x + (centerSVGCoord.x * scale - centerSVGCoord.x * nextScale);
    y = y + (centerSVGCoord.y * scale - centerSVGCoord.y * nextScale);
    this.setState({x, y, scale: nextScale});
  }

  public smoothZoomToSVGCoords(x: number, y: number, scale: number) {
    const el = this.element.current!;
    const ownerRect = el.getBoundingClientRect();
    x = -x * scale + ownerRect.width / 2;
    y = -y * scale + ownerRect.height / 2;

    this.smoothZoom({x, y, scale});
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

  onZoomAndCenter = (event: React.MouseEvent<HTMLDivElement>) => {
    const offset = this.screenToSVGCoords(this.getOffsetXY(event));
    if (Math.abs(DETAIL_ZOOM - this.state.scale) < 0.01) {
      this.smoothZoomToSVGCoords(offset.x, offset.y, this.state.minScale);
    } else {
      this.smoothZoomToSVGCoords(offset.x, offset.y, DETAIL_ZOOM);
    }
  };

  render() {
    const {children, onKeyDown, onDoubleClick, interactor, backgroundColor} = this.props;
    const {x, y, scale} = this.state;

    return (
      <div
        ref={this.element}
        style={Object.assign({backgroundColor}, SVGViewportStyles)}
        onMouseDown={(e) => interactor.onMouseDown(this, e)}
        onWheel={(e) => interactor.onWheel(this, e)}
        onDoubleClick={onDoubleClick}
        onKeyDown={onKeyDown}
        tabIndex={-1}
      >
        <div
          style={{
            transformOrigin: `top left`,
            transform: `matrix(${scale}, 0, 0, ${scale}, ${x}, ${y})`,
          }}
        >
          {children(this.state)}
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
};

const ZoomSliderContainer = styled.div`
  position: absolute;
  bottom: 0;
  right: 0;
  width: 30px;
  padding: 10px 8px;
  background: rgba(245, 248, 250, 0.4);
`;
