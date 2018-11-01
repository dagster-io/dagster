import * as React from "react";
import gql from "graphql-tag";
import { Colors } from "@blueprintjs/core";
import PipelineColorScale from "./PipelineColorScale";
import {
  SolidNodeFragment,
  SolidNodeFragment_inputs,
  SolidNodeFragment_outputs
} from "./types/SolidNodeFragment";
import { IFullSolidLayout, ILayout } from "./getFullSolidLayout";
import {
  SVGEllipseInRect,
  SVGFlowLayoutRect,
  SVGFlowLayoutFiller,
  SVGMonospaceText
} from "./SVGComponents";

interface ISolidNodeProps {
  layout: IFullSolidLayout;
  solid: SolidNodeFragment;
  minified: boolean;
  selected: boolean;
  dim: boolean;
  onClick?: (solid: string) => void;
  onDoubleClick?: (solid: string) => void;
}

interface ISolidTagsProps {
  x: number;
  y: number;
  width: number;
  minified: boolean;
  tags: string[];
}

function hueForTag(text = "") {
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
  minified
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
            stroke={`hsl(${hue}, 55%, 55%)`}
            strokeWidth={1}
            spacing={0}
          >
            <SVGMonospaceText
              text={tag}
              fill={`hsl(${hue}, 55%, 55%)`}
              size={minified ? 24 : 14}
            />
          </SVGFlowLayoutRect>
        );
      })}
    </SVGFlowLayoutRect>
  );
};

interface ISolidConfigNubProps {
  x: number;
  y: number;
  minified: boolean;
}

const SolidConfigNub: React.SFC<ISolidConfigNubProps> = ({
  x,
  y,
  minified
}) => {
  return (
    <>
      <SVGEllipseInRect
        x={x}
        y={y}
        width={26}
        height={26}
        stroke={Colors.GRAY3}
        fill={PipelineColorScale("solid")}
        pathLength={100}
        strokeWidth={1}
        strokeDasharray={`0 50 0`}
      />
      <SVGEllipseInRect
        x={x + 3}
        y={y + 3}
        width={20}
        height={20}
        stroke={Colors.WHITE}
        fill={PipelineColorScale("solidDarker")}
        pathLength={100}
        strokeWidth={2}
      />
      {!minified && (
        <text
          x={x + 8}
          y={y + 7.5}
          style={{ font: `14px "Arial", san-serif` }}
          fill={Colors.WHITE}
          dominantBaseline="hanging"
        >
          C
        </text>
      )}
    </>
  );
};

export default class SolidNode extends React.Component<ISolidNodeProps> {
  static fragments = {
    SolidNodeFragment: gql`
      fragment SolidNodeFragment on Solid {
        name
        inputs {
          definition {
            name
            type {
              name
            }
          }
          dependsOn {
            definition {
              name
            }
            solid {
              name
            }
          }
        }
        outputs {
          definition {
            name
            type {
              name
            }
            expectations {
              name
              description
            }
          }
        }
      }
    `
  };

  handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (this.props.onClick) {
      this.props.onClick(this.props.solid.name);
    }
  };

  handleDoubleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (this.props.onDoubleClick) {
      this.props.onDoubleClick(this.props.solid.name);
    }
  };

  renderIO(
    colorKey: string,
    items: Array<SolidNodeFragment_inputs | SolidNodeFragment_outputs>,
    layout: { [inputName: string]: { layout: ILayout } }
  ) {
    return Object.keys(layout).map((key, i) => {
      const { x, y, width, height } = layout[key].layout;
      const input = items.find(o => o.definition.name === key);
      const showText = width == 0 && !this.props.minified;

      return (
        <g key={i}>
          <SVGFlowLayoutRect
            x={x}
            y={y}
            stroke="#979797"
            strokeWidth={1}
            maxWidth={300}
            fill={PipelineColorScale(colorKey)}
            padding={8}
            spacing={7}
            height={height}
          >
            <SVGEllipseInRect
              width={14}
              height={14}
              fill="rgba(0, 0, 0, 0.3)"
              stroke="white"
              strokeWidth={1.5}
            />
            {showText && (
              <SVGMonospaceText
                text={`${input!.definition.name}:`}
                fill="#FFF"
                size={14}
              />
            )}
            {showText && (
              <SVGFlowLayoutRect
                rx={4}
                ry={4}
                stroke="#2491eb"
                strokeWidth={1}
                height={27}
                spacing={0}
                padding={4}
                fill="#d6ecff"
              >
                <SVGMonospaceText
                  text={input!.definition.type.name}
                  size={14}
                  fill="#222"
                />
              </SVGFlowLayoutRect>
            )}
          </SVGFlowLayoutRect>
        </g>
      );
    });
  }

  renderSelectedBox() {
    const { x, y, width, height } = this.props.layout.boundingBox;
    return (
      <rect
        x={x - 10}
        y={y - 10}
        width={width + 20}
        height={height + 20}
        stroke={Colors.GRAY3}
        fill="transparent"
        strokeWidth={this.props.minified ? 3 : 1}
        strokeDasharray={this.props.minified ? 12 : 4}
      />
    );
  }

  renderSolid() {
    return (
      <SVGFlowLayoutRect
        {...this.props.layout.solid}
        fill={PipelineColorScale("solid")}
        stroke="#979797"
        strokeWidth={1}
        spacing={0}
        padding={12}
      >
        <SVGMonospaceText
          size={this.props.minified ? 30 : 16}
          text={this.props.solid.name}
          fill={"#222"}
        />
      </SVGFlowLayoutRect>
    );
  }

  public render() {
    const { solid, layout, dim, selected, minified } = this.props;
    const { x, y, width, height } = layout.solid;

    return (
      <g
        onClick={this.handleClick}
        onDoubleClick={this.handleDoubleClick}
        opacity={dim ? 0.3 : 1}
      >
        {selected && this.renderSelectedBox()}
        {this.renderSolid()}
        {this.renderIO("input", solid.inputs, layout.inputs)}
        {this.renderIO("output", solid.outputs, layout.outputs)}
        <SolidConfigNub minified={minified} x={x + width - 33} y={y - 13} />
        <SolidTags
          x={x}
          y={y + height}
          width={width + 5}
          minified={minified}
          tags={["ipynb", "bla"]}
        />
      </g>
    );
  }
}
