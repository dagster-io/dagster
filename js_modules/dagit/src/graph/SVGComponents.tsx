import * as React from "react";

const PX_TO_UNITS = 0.62;

interface ISize {
  width: number;
  height: number;
  compressionPriority?: number;
}

export interface ISVGEllipseInRectProps
  extends React.SVGProps<SVGEllipseElement> {
  x?: number;
  y?: number;
  width: number;
  height: number;
}

/*
Wraps <ellipse>, but takes a width and height rather than center + radius,
making it compatible with SVGFlowLayoutRect (which inspects it's children's widths.)
*/
export class SVGEllipseInRect extends React.PureComponent<
  ISVGEllipseInRectProps
> {
  render() {
    const { width, height, x, y, ...rest } = this.props;
    const rx = width / 2;
    const ry = height / 2;
    return (
      <ellipse
        cx={(x || 0) + rx}
        cy={(y || 0) + ry}
        rx={rx}
        ry={ry}
        {...rest}
      />
    );
  }
}

export interface ISVGMonospaceTextProps {
  width?: number;
  size: number;
  text: string;
}

/*
Wraps <text>, exposes an intrinsic size and automatically truncates with ellipsis
if it's given a fixed width less than the space required for it's text.
*/
export class SVGMonospaceText extends React.PureComponent<
  ISVGMonospaceTextProps & React.SVGAttributes<SVGElement>
> {
  static intrinsicSizeForProps(props: ISVGMonospaceTextProps): ISize {
    return {
      width: Math.min(props.text.length * props.size * PX_TO_UNITS),
      height: props.size
    };
  }

  render() {
    const { width, size, text, ...rest } = this.props;
    const chars = width
      ? Math.round(width / (size * PX_TO_UNITS))
      : text.length;

    let textClipped = text;
    if (textClipped.length > chars) {
      textClipped = textClipped.substr(0, chars - 1) + "…";
    }

    return (
      <text
        {...rest}
        style={{
          font: `${size}px "Source Code Pro", monospace`,
          pointerEvents: "none"
        }}
        width={textClipped.length * size * PX_TO_UNITS}
        dominantBaseline="hanging"
      >
        {textClipped}
      </text>
    );
  }
}

export interface ISVGFlowLayoutRectProps {
  x?: number;
  y?: number;
  width?: number;
  height: number;
  padding: number;
  spacing: number;
  maxWidth?: number;
}

interface SVGFlowLayoutChildLayout {
  el: React.ReactElement<any>;
  width: number;
  height: number;
  compressionPriority: number;
}

function reactChildrenToArray(children: React.ReactNode) {
  let flattened: React.ReactNodeArray = [];

  const appendChildren = (arr: React.ReactNodeArray) => {
    arr.forEach(item => {
      if (!item) {
        return;
      }
      if (item instanceof Array) {
        appendChildren(item);
      } else {
        flattened.push(item);
      }
    });
  };

  appendChildren(children instanceof Array ? children : [children]);

  return flattened;
}
/*
Renders a <rect> and lays out it's children along a horizontal axis using the
given `padding` and inter-item `spacing`. Children must either have a `width`
prop or implement an `intrinsicSizeForProps` method that returns {width, height}.
Children are cloned and receive x, y, and width props from this parent.

If width or maxWidth is present, the SVGFlowLayoutRect evenly compresses
children that provided an instrinsic width rather than a fixed prop width to fit
in the available space. (TODO: Variable compression resistance?)
*/
export class SVGFlowLayoutRect extends React.Component<
  React.SVGAttributes<SVGElement> & ISVGFlowLayoutRectProps
> {
  static intrinsicSizeForProps(props: ISVGFlowLayoutRectProps): ISize {
    return SVGFlowLayoutRect.computeLayout(props);
  }

  static computeLayout(
    props: React.SVGAttributes<SVGElement> & ISVGFlowLayoutRectProps
  ): {
    width: number;
    height: number;
    childLayouts: Array<SVGFlowLayoutChildLayout>;
  } {
    let { children, spacing, padding, height } = props;

    const childLayouts = reactChildrenToArray(children).map(
      (el: React.ReactElement<any>) => {
        if (el.type && (el.type as any).intrinsicSizeForProps) {
          return {
            el,
            compressionPriority: 1,
            ...(el.type as any).intrinsicSizeForProps(el.props)
          };
        }
        if (!el.props || el.props.width === undefined) {
          console.error(el);
          throw new Error(
            `SVGFlowLayoutRect children must have a width prop or implement intrinsicSizeForProps`
          );
        }
        return {
          el: el,
          compressionPriority: 0,
          width: el.props.width,
          height: el.props.height
        };
      }
    );

    return {
      width:
        childLayouts.reduce((sum, dim) => sum + dim.width, 0) +
        padding * 2 +
        spacing * (childLayouts.length - 1),
      height: height,
      childLayouts: childLayouts
    };
  }

  render() {
    const { x, y, spacing, children, padding, maxWidth, ...rest } = this.props;
    const layout = SVGFlowLayoutRect.computeLayout(this.props);

    // Use the explicit width we're given, fall back to our intrinsic layout width
    const finalWidth = this.props.width
      ? this.props.width
      : Math.min(maxWidth || 10000, layout.width);

    // If the intrinsic layout width is greater than our final width, we need to
    // compress the child layouts to fit in available space. We compress children
    // with the highest compressionPriority first, distribute compression evenly
    // among children with that priority, and then work our way down in priority
    // until we've created enough space.
    if (layout.width > finalWidth) {
      const grouped: {
        [priority: string]: [SVGFlowLayoutChildLayout];
      } = {};

      // Group child layouts by compression priority
      layout.childLayouts.forEach(l => {
        const p = `${l.compressionPriority}`;
        grouped[p] = grouped[p] || [];
        grouped[p].push(l);
      });

      // Sort priority values so we shrink the most compressible nodes first
      const priorities = Object.keys(grouped).sort(
        (a, b) => parseInt(b) - parseInt(a)
      );

      for (let i = 0; i < priorities.length; i++) {
        const passLayouts = grouped[priorities[i]];
        const passWidth = passLayouts.reduce((sum, cl) => sum + cl.width, 0);
        const ratio =
          Math.max(1, passWidth - (layout.width - finalWidth)) / passWidth;
        if (ratio >= 0.99) break;

        passLayouts.forEach(childLayout => (childLayout.width *= ratio));
        layout.width -= passWidth * (1 - ratio);
      }
    }

    let acc = padding;

    // Clone our react children, applying `x`, `y`, and `width`, based on our
    // computed layout and the desired padding + inter-item spacing.
    const arranged = layout.childLayouts.map((childLayout, idx) => {
      const clone = React.cloneElement(childLayout.el, {
        x: (x || 0) + acc,
        y: (y || 0) + layout.height / 2 - childLayout.height / 2,
        width: childLayout.width,
        key: idx
      });

      acc += childLayout.width;
      if (idx + 1 < layout.childLayouts.length) {
        acc += spacing;
      }
      return clone;
    });

    acc += padding;

    return (
      <>
        <rect x={x} y={y} width={finalWidth} height={layout.height} {...rest} />
        {...arranged}
      </>
    );
  }
}

export class SVGFlowLayoutFiller extends React.PureComponent {
  static intrinsicSizeForProps(): ISize {
    return {
      compressionPriority: 2,
      width: 1000,
      height: 1
    };
  }
  render() {
    return <g />;
  }
}
