import * as React from "react";
import panzoom from "panzoom";

interface PanAndZoomProps {
  className?: string;
  graphWidth: number;
  graphHeight: number;
}

export default class PanAndZoom extends React.Component<PanAndZoomProps, {}> {
  element: React.RefObject<HTMLDivElement> = React.createRef();
  panzoom: any;

  componentDidMount() {
    if (this.element.current) {
      const el = this.element.current;
      const elWidth = el.clientWidth;
      const elHeight = el.clientHeight;
      const maxZoom = 1;
      let minZoom;
      minZoom = Math.min(
        el.clientWidth / this.props.graphWidth,
        el.clientHeight / this.props.graphHeight,
        1
      );

      this.panzoom = (panzoom(this.element.current, {
        smoothScroll: false,
        minZoom,
        maxZoom
      }) as any).zoomAbs(0, 0, minZoom);
    }
  }

  componentWillUnmount() {
    if (this.panzoom) {
      this.panzoom.dispose();
    }
  }

  render() {
    return (
      <div className={this.props.className} ref={this.element}>
        {this.props.children}
      </div>
    );
  }
}
