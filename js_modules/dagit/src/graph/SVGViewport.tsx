import * as React from "react";
import animate from "amator";

export interface SVGViewportInteractor {
  onMouseDown(
    viewport: SVGViewport,
    event: React.MouseEvent<HTMLDivElement>
  ): void;
  onWheel(viewport: SVGViewport, event: React.MouseEvent<HTMLDivElement>): void;
  render?(props: SVGViewportProps): React.ReactElement<any> | null;
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
export const MAX_OVERVIEW_ZOOM = 0.39;
export const MIN_OVERVIEW_ZOOM = 0.15;

const PanAndZoomInteractor: SVGViewportInteractor = {
  onMouseDown(viewport: SVGViewport, event: React.MouseEvent<HTMLDivElement>) {
    if (viewport._animation) {
      viewport._animation.cancel();
    }

    const start = viewport.getOffsetXY(event);
    let lastX: number = start.x;
    let lastY: number = start.y;

    const onMove = (e: MouseEvent) => {
      const offset = viewport.getOffsetXY(e);
      const delta = { x: offset.x - lastX, y: offset.y - lastY };
      viewport.setState({
        x: viewport.state.x + delta.x,
        y: viewport.state.y + delta.y
      });
      lastX = offset.x;
      lastY = offset.y;
    };

    const onUp = () => {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
    event.stopPropagation();
  },

  onWheel(viewport: SVGViewport, event: React.WheelEvent<HTMLDivElement>) {
    const offset = viewport.screenToSVGCoords(viewport.getOffsetXY(event));
    let { x, y, scale } = viewport.state;
    const oldScale = scale;

    scale = Math.max(
      0.015,
      Math.min(DETAIL_ZOOM, scale * (1 - event.deltaY * 0.0025))
    );
    x = x + (offset.x * oldScale - offset.x * scale);
    y = y + (offset.y * oldScale - offset.y * scale);

    viewport.setState({ x, y, scale });
  }
};

export default class SVGViewport extends React.Component<
  SVGViewportProps,
  SVGViewportState
> {
  static Interactors = {
    PanAndZoom: PanAndZoomInteractor
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
    minScale: 0
  };

  componentDidMount() {
    this.autocenter();
  }

  autocenter(animate = false) {
    const el = this.element.current!;
    const ownerRect = el.getBoundingClientRect();

    const dw = ownerRect.width / this.props.graphWidth;
    const dh = ownerRect.height / this.props.graphHeight;
    const desiredScale = Math.min(dw, dh);
    const boundedScale = Math.max(
      Math.min(desiredScale, MAX_OVERVIEW_ZOOM),
      MIN_OVERVIEW_ZOOM
    );

    if (this.state.scale < boundedScale && desiredScale !== boundedScale) {
      // If the user is zoomed out past where they're going to land, AND where they're going to land
      // is not a view of the entire DAG but instead a view of some zoomed section, autocentering is
      // undesirable and should do nothing.
      return;
    }
    const target = {
      x: -(this.props.graphWidth / 2) * boundedScale + ownerRect.width / 2,
      y: -(this.props.graphHeight / 2) * boundedScale + ownerRect.height / 2,
      scale: boundedScale
    };

    if (animate) {
      this.smoothZoom(target);
    } else {
      this.setState(Object.assign(target, { minScale: boundedScale }));
    }
  }

  screenToSVGCoords({ x, y }: Point): Point {
    const el = this.element.current!;
    const { width, height } = el.getBoundingClientRect();
    return {
      x: (-(this.state.x - width / 2) + x - width / 2) / this.state.scale,
      y: (-(this.state.y - height / 2) + y - height / 2) / this.state.scale
    };
  }

  getOffsetXY(e: MouseEvent | React.MouseEvent): Point {
    const el = this.element.current!;
    const ownerRect = el.getBoundingClientRect();
    return { x: e.clientX - ownerRect.left, y: e.clientY - ownerRect.top };
  }

  public smoothZoomToSVGCoords(x: number, y: number, scale: number) {
    const el = this.element.current!;
    const ownerRect = el.getBoundingClientRect();
    x = -x * scale + ownerRect.width / 2;
    y = -y * scale + ownerRect.height / 2;

    this.smoothZoom({ x, y, scale });
  }

  public smoothZoom(to: { x: number; y: number; scale: number }) {
    const from = { scale: this.state.scale, x: this.state.x, y: this.state.y };

    if (this._animation) {
      this._animation.cancel();
    }

    this._animation = animate(from, to, {
      step: (v: any) => {
        this.setState({
          x: v.x,
          y: v.y,
          scale: v.scale
        });
      },
      done: () => {
        this.setState(to);
        this._animation = null;
      }
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
    const {
      children,
      onKeyDown,
      onDoubleClick,
      interactor,
      backgroundColor
    } = this.props;
    const { x, y, scale } = this.state;

    return (
      <div
        ref={this.element}
        style={Object.assign({ backgroundColor }, SVGViewportStyles)}
        onMouseDown={e => interactor.onMouseDown(this, e)}
        onWheel={e => interactor.onWheel(this, e)}
        onDoubleClick={onDoubleClick}
        onKeyDown={onKeyDown}
        tabIndex={-1}
      >
        <div
          style={{
            transformOrigin: `top left`,
            transform: `matrix(${scale}, 0, 0, ${scale}, ${x}, ${y})`
          }}
        >
          {children(this.state)}
        </div>
        {interactor.render && interactor.render(this.props)}
      </div>
    );
  }
}

/*
BG: Not using styled-components here because I need a `ref` to an actual DOM element.
Styled-component with a ref returns a React component we need to findDOMNode to use.
*/
const SVGViewportStyles: React.CSSProperties = {
  width: "100%",
  height: "100%",
  position: "relative",
  overflow: "hidden",
  userSelect: "none"
};
