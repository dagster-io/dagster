import * as React from "react";
import animate from "amator";
import { Colors } from "@blueprintjs/core";

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
  interactor: SVGViewportInteractor;
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

const DETAIL_ZOOM = 1;
const MAX_OVERVIEW_ZOOM = 0.39;

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
    // Because of inertial scrolling on macOS, we receive wheel events for ~1000ms
    // after we trigger the zoom and this can cause a second zoom.
    const wheelWasIdle = Date.now() - viewport._lastWheelTime > 2000;
    const wheelChangedDir = viewport._lastWheelDir !== Math.sign(event.deltaY);

    // Ignore very gentle wheel interaction, could be accidental
    if (Math.abs(event.deltaY) <= 2) return;

    if (wheelWasIdle || wheelChangedDir) {
      if (event.deltaY < 0) {
        viewport.onZoomAndCenter(event);
      } else {
        viewport.autocenter(true);
      }
    }

    viewport._lastWheelTime = Date.now();
    viewport._lastWheelDir = Math.sign(event.deltaY);
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
  _lastWheelTime: number = 0;
  _lastWheelDir: number = 0;

  state = {
    x: 0,
    y: 0,
    scale: 1,
    minScale: 0
  };

  componentDidMount() {
    this.autocenter();
  }

  autocenter(animate: boolean = false) {
    const el = this.element.current!;
    const ownerRect = el.getBoundingClientRect();

    var dw = ownerRect.width / this.props.graphWidth;
    var dh = ownerRect.height / this.props.graphHeight;
    var scale = Math.min(dw, dh, MAX_OVERVIEW_ZOOM);

    const target = {
      x: -(this.props.graphWidth / 2) * scale + ownerRect.width / 2,
      y: -(this.props.graphHeight / 2) * scale + ownerRect.height / 2,
      scale: scale
    };

    if (animate) {
      this.smoothZoom(target);
    } else {
      this.setState(Object.assign(target, { minScale: scale }));
    }
  }

  screenToSVGCoords({ x, y }: Point): Point {
    const el = this.element.current!;
    var { width, height } = el.getBoundingClientRect();
    return {
      x: (-(this.state.x - width / 2) + x - width / 2) / this.state.scale,
      y: (-(this.state.y - height / 2) + y - height / 2) / this.state.scale
    };
  }

  getOffsetXY(e: MouseEvent | React.MouseEvent): Point {
    const el = this.element.current!;
    var ownerRect = el.getBoundingClientRect();
    return { x: e.clientX - ownerRect.left, y: e.clientY - ownerRect.top };
  }

  public smoothZoomToSVGCoords(x: number, y: number, targetScale: number) {
    const el = this.element.current!;
    var ownerRect = el.getBoundingClientRect();
    this.smoothZoom({
      x: -x * targetScale + ownerRect.width / 2,
      y: -y * targetScale + ownerRect.height / 2,
      scale: targetScale
    });
  }

  public smoothZoom(to: { x: number; y: number; scale: number }) {
    var from = { scale: this.state.scale, x: this.state.x, y: this.state.y };

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
        this._animation = null;
      }
    });
  }

  onZoomAndCenter = (event: React.MouseEvent<HTMLDivElement>) => {
    var offset = this.screenToSVGCoords(this.getOffsetXY(event));
    if (Math.abs(1 - this.state.scale) < 0.01) {
      this.smoothZoomToSVGCoords(offset.x, offset.y, this.state.minScale);
    } else {
      this.smoothZoomToSVGCoords(offset.x, offset.y, 1);
    }
  };

  render() {
    const { children, onKeyDown, interactor } = this.props;
    const { x, y, scale } = this.state;

    return (
      <div
        ref={this.element}
        style={SVGViewportStyles}
        onMouseDown={e => interactor.onMouseDown(this, e)}
        onWheel={e => interactor.onWheel(this, e)}
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
  userSelect: "none",
  backgroundColor: Colors.LIGHT_GRAY5
};
