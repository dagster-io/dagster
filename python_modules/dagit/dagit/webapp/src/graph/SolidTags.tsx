import * as React from "react";
import {
  SVGFlowLayoutRect,
  SVGFlowLayoutFiller,
  SVGMonospaceText
} from "./SVGComponents";

export interface ISolidTagsProps {
  x: number;
  y: number;
  width: number;
  minified: boolean;
  tags: string[];
  onTagClicked: ((e: React.MouseEvent, tag: string) => void);
}

function hueForTag(text = "") {
  if (text === "ipynb") return 26;
  return (
    text
      .split("")
      .map(c => c.charCodeAt(0))
      .reduce((n, a) => n + a) % 360
  );
}

const SolidTags: React.SFC<ISolidTagsProps> = ({
  tags,
  x,
  y,
  width,
  minified,
  onTagClicked
}) => {
  const height = minified ? 32 : 20;
  const overhang = 6;

  return (
    <SVGFlowLayoutRect
      x={x}
      y={y - (height - overhang)}
      width={width}
      height={height}
      fill={"transparent"}
      stroke={"transparent"}
      spacing={minified ? 8 : 4}
      padding={0}
    >
      <SVGFlowLayoutFiller />
      {tags.map(tag => {
        const hue = hueForTag(tag);
        return (
          <SVGFlowLayoutRect
            key={tag}
            rx={0}
            ry={0}
            height={height}
            padding={minified ? 8 : 4}
            fill={`hsl(${hue}, 10%, 95%)`}
            stroke={`hsl(${hue}, 75%, 55%)`}
            onClick={e => onTagClicked(e, tag)}
            strokeWidth={1}
            spacing={0}
          >
            <SVGMonospaceText
              text={tag}
              fill={`hsl(${hue}, 75%, 55%)`}
              size={minified ? 24 : 14}
            />
          </SVGFlowLayoutRect>
        );
      })}
    </SVGFlowLayoutRect>
  );
};

export default SolidTags;
