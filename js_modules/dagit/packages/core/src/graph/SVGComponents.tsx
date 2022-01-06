import * as React from 'react';

import {FontFamily} from '../ui/styles';

const PX_TO_UNITS = 0.53;

interface ISize {
  width: number;
  height: number;
  compressionPriority?: number;
}

interface ISVGMonospaceTextProps {
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
      fontFamily: FontFamily.monospace,
      fontSize: `${size}px`,
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

export const SVGLabeledRect: React.FC<{
  x: number;
  y: number;
  minified: boolean;
  width: number;
  height: number;
  label: string;
  fill: string;
  className?: string;
}> = ({minified, label, fill, className, ...rect}) => (
  <g>
    <rect {...rect} fill={fill} stroke="#979797" strokeWidth={1} className={className} />
    <SVGMonospaceText
      x={rect.x + (minified ? 10 : 5)}
      y={rect.y + (minified ? 10 : 5)}
      height={undefined}
      size={minified ? 30 : 16}
      text={label}
      fill="#979797"
    />
  </g>
);
