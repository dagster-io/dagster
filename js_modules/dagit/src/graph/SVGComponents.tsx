import * as React from 'react';

const PX_TO_UNITS = 0.62;

interface ISize {
  width: number;
  height: number;
  compressionPriority?: number;
}

export interface ISVGEllipseInRectProps extends React.SVGProps<SVGEllipseElement> {
  x?: number;
  y?: number;
  width: number;
  height: number;
}

/*
Wraps <ellipse>, but takes a width and height rather than center + radius,
making it compatible with SVGFlowLayoutRect (which inspects it's children's widths.)
*/
export class SVGEllipseInRect extends React.PureComponent<ISVGEllipseInRectProps> {
  render() {
    const {width, height, x, y, ...rest} = this.props;
    const rx = width / 2;
    const ry = height / 2;
    return <ellipse cx={(x || 0) + rx} cy={(y || 0) + ry} rx={rx} ry={ry} {...rest} />;
  }
}

export interface ISVGMonospaceTextProps {
  width?: number;
  size: number;
  text: string;
  allowTwoLines?: boolean;
}

const LINE_SPACING = 1.25;

const clipToLength = (str: string, len: number) => {
  return str.length > len ? str.substr(0, len - 1) + '…' : str;
};

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
      height: props.size,
    };
  }

  render() {
    const {y, width, size, text, allowTwoLines, ...rest} = this.props;

    const lineChars = width ? Math.round(width / (size * PX_TO_UNITS)) : text.length;
    let line1 = '';
    let line2 = '';

    if (allowTwoLines) {
      const parts = text.split('_');
      while (parts.length && line1.length + parts[0].length <= lineChars) {
        line1 += parts.shift() + (parts.length > 0 ? '_' : '');
      }
      line2 = clipToLength(parts.join('_'), lineChars);
    } else {
      line1 = clipToLength(text, lineChars);
    }

    const line1Y = (Number(y) || 0) - (line2.length > 0 ? (Number(size) * LINE_SPACING) / 2 : 0);

    const style: React.CSSProperties = {
      font: `${size}px "Source Code Pro", monospace`,
      pointerEvents: 'none',
    };

    return (
      <>
        <text
          {...rest}
          y={line1Y}
          style={style}
          width={line1.length * size * PX_TO_UNITS}
          height={size}
          dominantBaseline="hanging"
        >
          {line1}
        </text>
        {line2 && (
          <text
            {...rest}
            y={line1Y + Number(size) * LINE_SPACING}
            style={style}
            width={line2.length * size * PX_TO_UNITS}
            height={size}
            dominantBaseline="hanging"
          >
            {line2}
          </text>
        )}
      </>
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
  const flattened: React.ReactNodeArray = [];

  const appendChildren = (arr: React.ReactNodeArray) => {
    arr.forEach((item) => {
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
children that provided an intrinsic width rather than a fixed prop width to fit
in the available space. (TODO: Variable compression resistance?)
*/
export class SVGFlowLayoutRect extends React.Component<
  React.SVGAttributes<SVGElement> & ISVGFlowLayoutRectProps
> {
  static intrinsicSizeForProps(props: ISVGFlowLayoutRectProps): ISize {
    return SVGFlowLayoutRect.computeLayout(props);
  }

  static computeLayout(
    props: React.SVGAttributes<SVGElement> & ISVGFlowLayoutRectProps,
  ): {
    width: number;
    height: number;
    childLayouts: Array<SVGFlowLayoutChildLayout>;
  } {
    const {children, spacing, padding, height} = props;

    const childLayouts = reactChildrenToArray(children).map((el: React.ReactElement<any>) => {
      if (el.type && (el.type as any).intrinsicSizeForProps) {
        return {
          el,
          compressionPriority: 1,
          ...(el.type as any).intrinsicSizeForProps(el.props),
        };
      }
      if (!el.props || el.props.width === undefined) {
        console.error(el);
        throw new Error(
          `SVGFlowLayoutRect children must have a width prop or implement intrinsicSizeForProps`,
        );
      }
      return {
        el: el,
        compressionPriority: 0,
        width: el.props.width,
        height: el.props.height,
      };
    });

    return {
      width:
        childLayouts.reduce((sum, dim) => sum + dim.width, 0) +
        padding * 2 +
        spacing * (childLayouts.length - 1),
      height: height,
      childLayouts: childLayouts,
    };
  }

  render() {
    const {x, y, spacing, padding, maxWidth, ...rest} = this.props;
    const layout = SVGFlowLayoutRect.computeLayout(this.props);
    rest.children = [];

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
        [priority: string]: SVGFlowLayoutChildLayout[];
      } = {};

      // Group child layouts by compression priority
      layout.childLayouts.forEach((l) => {
        const p = `${l.compressionPriority}`;
        grouped[p] = grouped[p] || [];
        grouped[p].push(l);
      });

      // Sort priority values so we shrink the most compressible nodes first
      const priorities = Object.keys(grouped).sort((a, b) => parseInt(b) - parseInt(a));

      for (let i = 0; i < priorities.length; i++) {
        const passLayouts = grouped[priorities[i]];
        const passWidth = passLayouts.reduce((sum, cl) => sum + cl.width, 0);
        const ratio = Math.max(1, passWidth - (layout.width - finalWidth)) / passWidth;
        if (ratio >= 0.99) break;

        passLayouts.forEach((childLayout) => (childLayout.width *= ratio));
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
        key: idx,
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
        {arranged}
      </>
    );
  }
}

export class SVGFlowLayoutFiller extends React.PureComponent {
  static intrinsicSizeForProps(): ISize {
    return {
      compressionPriority: 2,
      width: 1000,
      height: 1,
    };
  }
  render() {
    return <g />;
  }
}

interface SVGLabeledRectProps {
  x: number;
  y: number;
  minified: boolean;
  width: number;
  height: number;
  label: string;
  fill: string;
  className?: string;
}

export const SVGLabeledRect: React.FunctionComponent<SVGLabeledRectProps> = ({
  minified,
  label,
  fill,
  className,
  ...rect
}) => (
  <g>
    <rect {...rect} fill={fill} stroke="#979797" strokeWidth={1} className={className} />
    <SVGMonospaceText
      x={rect.x + (minified ? 10 : 5)}
      y={rect.y + (minified ? 10 : 5)}
      height={undefined}
      size={minified ? 30 : 16}
      text={label}
      fill={'#979797'}
    />
  </g>
);
