// Adopted from https://github.com/woutervh-/react-pan-and-zoom-hoc

import * as React from "react";

export interface PanAndZoomProps {
  x?: number;
  y?: number;
  scale?: number;
  scaleFactor?: number;
  minScale?: number;
  maxScale?: number;
  renderOnChange?: boolean;
  passOnProps?: boolean;
  ignorePanOutside?: boolean;
  onPanStart?: (
    event: React.MouseEvent | React.TouchEvent | MouseEvent | TouchEvent
  ) => void;
  onPanMove?: (
    x: number,
    y: number,
    event: React.MouseEvent | React.TouchEvent | MouseEvent | TouchEvent
  ) => void;
  onPanEnd?: (
    x: number,
    y: number,
    event: React.MouseEvent | React.TouchEvent | MouseEvent | TouchEvent
  ) => void;
  onZoom?: (
    x: number | undefined,
    y: number | undefined,
    scale: number | undefined,
    event: React.WheelEvent | WheelEvent
  ) => void;
  onPanAndZoom?: (
    x: number,
    y: number,
    scale: number,
    event: React.WheelEvent | WheelEvent
  ) => void;
}

export default class PanAndZoom extends React.Component<PanAndZoomProps, any> {
  static defaultProps = {
    x: 0.5,
    y: 0.5,
    scale: 1,
    scaleFactor: Math.sqrt(2),
    minScale: Number.EPSILON,
    maxScale: Number.POSITIVE_INFINITY,
    renderOnChange: false,
    passOnProps: false
  };

  dx: number = 0;
  dy: number = 0;
  ds: number = 0;
  element: HTMLElement | null = null;

  componentWillReceiveProps(nextProps: PanAndZoomProps) {
    if (this.props.x !== nextProps.x || this.props.y !== nextProps.y) {
      this.dx = 0;
      this.dy = 0;
    }
    if (this.props.scale !== nextProps.scale) {
      this.ds = 0;
    }
  }

  componentWillUnmount() {
    // if (this.panning) {
    //   document.removeEventListener("mousemove", this.handleMouseMove);
    //   document.removeEventListener("mouseup", this.handleMouseUp);
    //   document.removeEventListener("touchmove", this.handleMouseMove);
    //   document.removeEventListener("touchend", this.handleMouseUp);
    // }
  }

  handleWheel = (event: React.WheelEvent | WheelEvent) => {
    const { onPanAndZoom, renderOnChange, onZoom } = this.props;
    const x: number | undefined = this.props.x;
    const y: number | undefined = this.props.y;
    const scale: number | undefined = this.props.scale;
    const scaleFactor: number | undefined = this.props.scaleFactor;
    const minScale: number | undefined = this.props.minScale;
    const maxScale: number | undefined = this.props.maxScale;

    if (
      x !== undefined &&
      y !== undefined &&
      scale !== undefined &&
      scaleFactor !== undefined &&
      minScale !== undefined &&
      maxScale !== undefined
    ) {
      const { deltaY } = event;
      const newScale =
        deltaY < 0
          ? Math.min((scale + this.ds) * scaleFactor, maxScale)
          : Math.max((scale + this.ds) / scaleFactor, minScale);
      const factor = newScale / (scale + this.ds);

      if (factor !== 1) {
        const target = this.element;
        if (!target) {
          return;
        }
        const dimensions = target.getBoundingClientRect();
        if (dimensions) {
          const { width, height } = dimensions;
          const { clientX, clientY } = this.normalizeTouchPosition(
            event,
            target as HTMLElement
          );
          const dx = (clientX / width - 0.5) / (scale + this.ds);
          const dy = (clientY / height - 0.5) / (scale + this.ds);
          const sdx = dx * (1 - 1 / factor);
          const sdy = dy * (1 - 1 / factor);

          this.dx += sdx;
          this.dy += sdy;
          this.ds = newScale - scale;

          if (onPanAndZoom) {
            onPanAndZoom(x + this.dx, y + this.dy, scale + this.ds, event);
          }

          if (renderOnChange) {
            this.forceUpdate();
          }
        }
      }
    }

    if (onZoom) {
      onZoom(x, y, scale, event);
    }

    event.preventDefault();
  };

  panning = false;
  panLastX = 0;
  panLastY = 0;

  handleMouseDown = (event: React.MouseEvent | React.TouchEvent) => {
    if (!this.panning) {
      const { onPanStart } = this.props;
      const target = this.element;
      if (!target) {
        return;
      }
      const { clientX, clientY } = this.normalizeTouchPosition(event, target);
      this.panLastX = clientX;
      this.panLastY = clientY;
      this.panning = true;

      document.addEventListener("mousemove", this.handleMouseMove);
      document.addEventListener("mouseup", this.handleMouseUp);
      document.addEventListener("touchmove", this.handleMouseMove);
      document.addEventListener("touchend", this.handleMouseUp);

      if (onPanStart) {
        onPanStart(event);
      }
    }
  };

  handleMouseMove = (
    event: React.MouseEvent | React.TouchEvent | MouseEvent | TouchEvent
  ) => {
    if (this.panning) {
      const { onPanMove, renderOnChange, ignorePanOutside } = this.props;
      const x: number | undefined = this.props.x;
      const y: number | undefined = this.props.y;
      const scale: number | undefined = this.props.scale;

      if (x !== undefined && y !== undefined && scale !== undefined) {
        const target = this.element;
        if (!target) {
          return;
        }
        const { clientX, clientY } = this.normalizeTouchPosition(event, target);
        const { width, height } = target.getBoundingClientRect();

        if (
          !ignorePanOutside ||
          (0 <= clientX &&
            clientX <= width &&
            0 <= clientY &&
            clientY <= height)
        ) {
          const dx = clientX - this.panLastX;
          const dy = clientY - this.panLastY;
          this.panLastX = clientX;
          this.panLastY = clientY;
          const sdx = dx / (width * (scale + this.ds));
          const sdy = dy / (height * (scale + this.ds));
          this.dx -= sdx;
          this.dy -= sdy;

          if (onPanMove) {
            onPanMove(x + this.dx, y + this.dy, event);
          }

          if (renderOnChange) {
            this.forceUpdate();
          }
        }
      }
    }
  };

  handleMouseUp = (
    event: React.MouseEvent | React.TouchEvent | MouseEvent | TouchEvent
  ) => {
    if (this.panning) {
      const { onPanEnd, renderOnChange, ignorePanOutside } = this.props;
      const x: number | undefined = this.props.x;
      const y: number | undefined = this.props.y;
      const scale: number | undefined = this.props.scale;

      document.removeEventListener("mousemove", this.handleMouseMove);
      document.removeEventListener("mouseup", this.handleMouseUp);
      document.removeEventListener("touchmove", this.handleMouseMove);
      document.removeEventListener("touchend", this.handleMouseUp);

      if (x !== undefined && y !== undefined && scale !== undefined) {
        const target = this.element;
        if (!target) {
          return;
        }
        try {
          const { clientX, clientY } = this.normalizeTouchPosition(
            event,
            target as HTMLElement
          );
          const dimensions = target.getBoundingClientRect();
          if (dimensions) {
            const { width, height } = dimensions;

            if (
              !ignorePanOutside ||
              (0 <= clientX &&
                clientX <= width &&
                0 <= clientY &&
                clientY <= height)
            ) {
              const dx = clientX - this.panLastX;
              const dy = clientY - this.panLastY;
              this.panLastX = clientX;
              this.panLastY = clientY;
              const sdx = dx / (width * (scale + this.ds));
              const sdy = dy / (height * (scale + this.ds));
              this.dx -= sdx;
              this.dy -= sdy;
            }
          }
        } catch (error) {
          // Happens when touches are used
        }

        this.panning = false;

        if (onPanEnd) {
          onPanEnd(x + this.dx, y + this.dy, event);
        }

        if (renderOnChange) {
          this.forceUpdate();
        }
      }
    }
  };

  normalizeTouchPosition(
    event: React.MouseEvent | React.TouchEvent | MouseEvent | TouchEvent,
    parent: HTMLElement
  ) {
    const position = {
      clientX:
        "targetTouches" in event ? event.targetTouches[0].pageX : event.clientX,
      clientY:
        "targetTouches" in event ? event.targetTouches[0].pageY : event.clientY
    };

    while (parent.offsetParent) {
      position.clientX -= parent.offsetLeft - parent.scrollLeft;
      position.clientY -= parent.offsetTop - parent.scrollTop;

      parent = parent.offsetParent as HTMLElement;
    }

    return position;
  }

  render() {
    const {
      children,
      scaleFactor,
      x: tempX,
      y: tempY,
      scale: tempScale,
      minScale,
      maxScale,
      onPanStart,
      onPanMove,
      onPanEnd,
      onZoom,
      onPanAndZoom,
      renderOnChange,
      passOnProps,
      ignorePanOutside,
      ...other
    } = this.props;
    let x: number | undefined = this.props.x;
    let y: number | undefined = this.props.y;
    let scale: number | undefined = this.props.scale;

    if (x !== undefined && y !== undefined && scale !== undefined) {
      x = x + this.dx;
      y = y + this.dy;
      scale = scale + this.ds;

      return (
        <div
          ref={el => {
            this.element = el;
          }}
          {...other}
          onMouseDown={this.handleMouseDown}
          onTouchStart={this.handleMouseDown}
          onWheel={this.handleWheel}
        >
          <div
            style={{
              transform: `scale(${scale}, ${scale}) translate3d(${(0.5 - x) *
                1500}px, ${(0.5 - y) * 1500}px, 0)`,
              width: "100%",
              height: "100%"
            }}
          >
            {children}
          </div>
        </div>
      );
    } else {
      return null;
    }
  }
}
