import * as React from "react";
import gql from "graphql-tag";
import { isEqual, omitBy } from "lodash";
import { Colors } from "@blueprintjs/core";
import PipelineColorScale from "./PipelineColorScale";
import { IFullSolidLayout, ILayout } from "./getFullSolidLayout";
import {
  SolidNodeFragment,
  SolidNodeFragment_inputs,
  SolidNodeFragment_outputs
} from "./types/SolidNodeFragment";
import {
  SVGEllipseInRect,
  SVGFlowLayoutRect,
  SVGMonospaceText
} from "./SVGComponents";

import SolidTags from "./SolidTags";
import SolidConfigPort from "./SolidConfigPort";
import { DEFAULT_RESULT_NAME } from "../Util";
import { number } from "prop-types";

interface ISolidNodeProps {
  layout: IFullSolidLayout;
  solid: SolidNodeFragment;
  parentSolid?: SolidNodeFragment;
  highlightedConnections: { a: string; b: string }[];
  minified: boolean;
  selected: boolean;
  dim: boolean;
  onClick: (solidName: string) => void;
  onDoubleClick: (solidName: string) => void;
  onHighlightConnections: (conns: { a: string; b: string }[]) => void;
}

export default class SolidNode extends React.Component<ISolidNodeProps> {
  static fragments = {
    SolidNodeFragment: gql`
      fragment SolidNodeFragment on Solid {
        name
        definition {
          __typename
          metadata {
            key
            value
          }
          ... on SolidDefinition {
            configDefinition {
              configType {
                name
                description
              }
            }
          }
          ... on CompositeSolidDefinition {
            inputMappings {
              definition {
                name
              }
              mappedInput {
                definition {
                  name
                }
                solid {
                  name
                }
              }
            }
            outputMappings {
              definition {
                name
              }
              mappedOutput {
                definition {
                  name
                }
                solid {
                  name
                }
              }
            }
          }
        }
        inputs {
          definition {
            name
            type {
              displayName
              isNothing
            }
          }
          dependsOn {
            definition {
              name
              type {
                displayName
              }
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
              displayName
              isNothing
            }
            expectations {
              name
              description
            }
          }
          dependedBy {
            solid {
              name
            }
            definition {
              name
              type {
                displayName
              }
            }
          }
        }
      }
    `
  };

  shouldComponentUpdate(prevProps: ISolidNodeProps) {
    return !isEqual(
      omitBy(prevProps, v => typeof v === "function"),
      omitBy(this.props, v => typeof v === "function")
    );
  }

  handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    this.props.onClick(this.props.solid.name);
  };

  handleDoubleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    this.props.onDoubleClick(this.props.solid.name);
  };

  handleKindClicked = (e: React.MouseEvent, kind: string) => {
    this.handleClick(e);
    window.requestAnimationFrame(() =>
      document.dispatchEvent(new Event("show-kind-info"))
    );
  };

  renderIO(
    colorKey: string,
    items: Array<SolidNodeFragment_inputs | SolidNodeFragment_outputs>,
    layout: { [ioName: string]: { layout: ILayout } }
  ) {
    const { solid, parentSolid, minified, highlightedConnections } = this.props;

    return Object.keys(layout).map((key, i) => {
      const { x, y, width, height } = layout[key].layout;

      const item = items.find(o => o.definition.name === key);
      if (!item) return <g key={i} />;

      const { name, type } = item.definition;
      const showText = width == 0 && !minified;

      const connections: Array<{ a: string; b: string }> = [];
      let title = `${name}: ${type.displayName}`;
      let clickTarget: string | null = null;
      let mapping: { definition: { name: string } } | undefined = undefined;

      if ("dependsOn" in item && item.dependsOn) {
        title +=
          `\n\nFrom:\n` +
          item.dependsOn
            .map(o => `${o.solid.name}: ${o.definition.name}`)
            .join("\n");
        clickTarget =
          item.dependsOn.length === 1 ? item.dependsOn[0].solid.name : null;

        mapping =
          parentSolid &&
          parentSolid.definition.__typename === "CompositeSolidDefinition"
            ? parentSolid.definition.inputMappings.find(
                m =>
                  m.mappedInput.solid.name === solid.name &&
                  m.mappedInput.definition.name === key
              )
            : undefined;

        connections.push(
          ...item.dependsOn.map(o => ({
            a: o.solid.name,
            b: solid.name
          }))
        );
      }
      if ("dependedBy" in item) {
        title +=
          "\n\nUsed By:\n" +
          item.dependedBy
            .map(o => `${o.solid.name} ${o.definition.name}`)
            .join("\n");
        clickTarget =
          item.dependedBy.length === 1 ? item.dependedBy[0].solid.name : null;

        mapping =
          parentSolid &&
          parentSolid.definition.__typename === "CompositeSolidDefinition"
            ? parentSolid.definition.outputMappings.find(
                m =>
                  m.mappedOutput.solid.name === solid.name &&
                  m.mappedOutput.definition.name === key
              )
            : undefined;

        connections.push(
          ...item.dependedBy.map(o => ({
            a: o.solid.name,
            b: solid.name
          }))
        );
      }

      const highlighted = connections.some(
        ({ a, b }) =>
          !!highlightedConnections.find(
            h => (h.a === a || h.a === b) && (h.b === a || h.b === b)
          )
      );

      return (
        <g
          key={i}
          onMouseEnter={() => this.props.onHighlightConnections(connections)}
          onMouseLeave={() => this.props.onHighlightConnections([])}
          onClick={() => clickTarget && this.props.onDoubleClick(clickTarget)}
        >
          <title>{title}</title>
          {mapping && (
            <ExternalMappingDot
              rx={x + 8 + 7}
              ry={y + 8 + 7}
              length={45}
              direction={"dependedBy" in item ? 1 : -1}
              minified={minified}
              text={mapping.definition.name}
            />
          )}
          <SVGFlowLayoutRect
            x={x}
            y={y}
            stroke="#979797"
            strokeWidth={1}
            maxWidth={300}
            fill={
              highlighted
                ? PipelineColorScale(`${colorKey}Highlighted`)
                : PipelineColorScale(colorKey)
            }
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
            {showText && name !== DEFAULT_RESULT_NAME && (
              <SVGMonospaceText text={`${name}:`} fill="#FFF" size={14} />
            )}
            {showText && type.displayName && (
              <SVGFlowLayoutRect
                rx={4}
                ry={4}
                fill="#d6ecff"
                stroke="#2491eb"
                strokeWidth={1}
                height={27}
                spacing={0}
                padding={4}
              >
                <SVGMonospaceText
                  text={type.displayName}
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
        stroke="rgba(255, 69, 0, 1)"
        fill="rgba(255, 69, 0, 0.2)"
        strokeWidth={this.props.minified ? 8 : 3}
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

  public renderCompositeMark() {
    const { x, y, width, height } = this.props.layout.solid;
    return (
      <rect
        x={x - 6}
        y={y - 6}
        width={width + 12}
        height={height + 12}
        fill={PipelineColorScale("solid")}
        stroke="#979797"
        strokeWidth={1}
      />
    );
  }

  public render() {
    const { solid, layout, dim, selected, minified } = this.props;
    const { metadata } = solid.definition;
    const { x, y, width, height } = layout.solid;

    console.log(solid);

    let configDefinition = null;
    if (solid.definition.__typename === "SolidDefinition") {
      configDefinition = solid.definition.configDefinition;
    }

    const kind = metadata.find(m => m.key === "kind");

    return (
      <g
        onClick={this.handleClick}
        onDoubleClick={this.handleDoubleClick}
        opacity={dim ? 0.3 : 1}
      >
        {selected && this.renderSelectedBox()}
        {solid.definition.__typename === "CompositeSolidDefinition" &&
          this.renderCompositeMark()}
        {this.renderSolid()}
        {this.renderIO("input", solid.inputs, layout.inputs)}
        {this.renderIO("output", solid.outputs, layout.outputs)}
        {configDefinition && (
          <SolidConfigPort x={x + width - 33} y={y - 13} minified={minified} />
        )}
        {kind && kind.value && (
          <SolidTags
            x={x}
            y={y + height}
            width={width + 5}
            minified={minified}
            tags={[kind.value]}
            onTagClicked={this.handleKindClicked}
          />
        )}
      </g>
    );
  }
}

interface ExternalMappingDotProps {
  rx: number;
  ry: number;
  minified: boolean;
  length: number;
  direction: -1 | 1;
  text: string;
}

const ExternalMappingDot = ({
  rx,
  ry,
  minified,
  length,
  direction,
  text
}: ExternalMappingDotProps) => {
  const textSize = SVGMonospaceText.intrinsicSizeForProps({ size: 14, text });
  const dotRadius = 10;
  const dotCX = rx - length;
  const dotCY = ry + length * direction;

  return (
    <g>
      <line
        stroke={Colors.VIOLET3}
        strokeWidth={4}
        x1={rx}
        y1={ry}
        x2={dotCX}
        y2={dotCY}
      />
      {!minified && (
        <SVGMonospaceText
          x={dotCX - (textSize.width + dotRadius + 4)}
          y={dotCY - textSize.height / 2}
          text={text}
          fill={Colors.VIOLET3}
          size={14}
        />
      )}
      <ellipse
        fill={Colors.VIOLET3}
        cx={dotCX}
        cy={dotCY}
        rx={dotRadius}
        ry={dotRadius}
      />
    </g>
  );
};
