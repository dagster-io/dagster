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

interface ISolidNodeProps {
  layout: IFullSolidLayout;
  solid: SolidNodeFragment;
  minified: boolean;
  selected: boolean;
  dim: boolean;
  onClick?: (solid: string) => void;
  onDoubleClick?: (solid: string) => void;
}

interface ITextDimensions {
  text: string;
  textSize: number;
  maxWidth: number;
}

const PX_TO_UNITS = 0.62;

function measureAndClip({
  text,
  textSize,
  maxWidth
}: ITextDimensions): { text: string; width: number } {
  const chars = maxWidth / (textSize * PX_TO_UNITS);
  let textClipped = text;
  if (textClipped.length > chars) {
    textClipped = textClipped.substr(0, chars - 1) + "…";
  }
  return {
    width: textClipped.length * textSize * PX_TO_UNITS,
    text: textClipped
  };
}

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

      const portInset = 9;
      const portRadius = 7;
      const textSize = 15;
      const namePadding = 7;
      const typePadding = 4;
      const name = measureAndClip({
        text: `${input!.definition.name}: `,
        textSize,
        maxWidth: 200
      });
      const type = measureAndClip({
        text: input!.definition.type.name,
        textSize,
        maxWidth: 200
      });

      const baseline = y + height / 2 + textSize / 2;

      let containerWidth =
        portInset +
        portRadius * 2 +
        namePadding +
        name.width +
        typePadding +
        type.width +
        typePadding +
        namePadding;

      if (this.props.minified) {
        containerWidth = 30;
      }

      return (
        <g key={i}>
          <rect
            x={x}
            y={y}
            stroke="#979797"
            strokeWidth={1}
            width={width || containerWidth}
            height={height}
            fill={PipelineColorScale(colorKey)}
          />
          <ellipse
            cx={x + portInset + portRadius}
            cy={y + height / 2}
            rx={portRadius}
            ry={portRadius}
            fill="rgba(0, 0, 0, 0.3)"
            stroke="white"
          />
          {width == 0 &&
            !this.props.minified && (
              <text
                x={x + portInset + portRadius * 2 + namePadding}
                y={baseline}
                fill="white"
                style={{ font: `${textSize}px "Source Code Pro", monospace` }}
              >
                {name.text}
              </text>
            )}
          {width == 0 &&
            !this.props.minified && (
              <>
                <rect
                  x={x + portInset + portRadius * 2 + namePadding + name.width}
                  y={y + 5}
                  rx={4}
                  ry={4}
                  stroke="#2491eb"
                  strokeWidth={1}
                  width={type.width + typePadding * 2}
                  height={27}
                  fill="#d6ecff"
                />
                <text
                  x={
                    x +
                    portInset +
                    portRadius * 2 +
                    namePadding +
                    name.width +
                    typePadding
                  }
                  y={baseline}
                  style={{
                    font: `500 ${textSize}px "Source Code Pro", monospace`
                  }}
                  fill="#222"
                >
                  {type.text}
                </text>
              </>
            )}
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
    const textPadding = 12;
    const textSize = this.props.minified ? 30 : 16;
    const bounds = this.props.layout.solid;
    const name = measureAndClip({
      maxWidth: bounds.width - textPadding * 2,
      text: this.props.solid.name,
      textSize
    });

    return (
      <>
        <rect
          {...bounds}
          fill={PipelineColorScale("solid")}
          stroke="#979797"
          strokeWidth={1}
        />
        <text
          x={bounds.x + textPadding}
          y={bounds.y + bounds.height / 2 + textSize / 2}
          style={{ font: `500 ${textSize}px "Source Code Pro", monospace` }}
        >
          {name.text}
        </text>
      </>
    );
  }

  public render() {
    const { solid, layout } = this.props;

    return (
      <g
        onClick={this.handleClick}
        onDoubleClick={this.handleDoubleClick}
        opacity={this.props.dim ? 0.3 : 1}
      >
        {this.props.selected && this.renderSelectedBox()}
        {this.renderSolid()}
        {this.renderIO("input", solid.inputs, layout.inputs)}
        {this.renderIO("output", solid.outputs, layout.outputs)}
      </g>
    );
  }
}
