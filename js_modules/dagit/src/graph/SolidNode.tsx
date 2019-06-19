import * as React from "react";
import gql from "graphql-tag";
import { isEqual, omitBy } from "lodash";
import PipelineColorScale from "./PipelineColorScale";
import { IFullSolidLayout } from "./getFullSolidLayout";
import { SolidNodeFragment } from "./types/SolidNodeFragment";
import { SVGFlowLayoutRect, SVGMonospaceText } from "./SVGComponents";

import SolidTags, { ISolidTag } from "./SolidTags";
import { SolidConfigPort } from "./SolidConfigPort";
import { SolidIOBox, metadataForIO } from "./SolidIOBox";
import { Edge } from "./highlighting";

interface ISolidNodeProps {
  layout: IFullSolidLayout;
  solid: SolidNodeFragment;
  parentSolid?: SolidNodeFragment;
  highlightedEdges: Edge[];
  minified: boolean;
  selected: boolean;
  dim: boolean;
  onClick: (solidName: string) => void;
  onDoubleClick: (solidName: string) => void;
  onEnterComposite: (solidName: string) => void;
  onHighlightEdges: (edges: Edge[]) => void;
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

  handleEnterComposite = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    this.props.onEnterComposite(this.props.solid.name);
  };

  handleKindClicked = (e: React.MouseEvent) => {
    this.handleClick(e);
    window.requestAnimationFrame(() =>
      document.dispatchEvent(new Event("show-kind-info"))
    );
  };

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
        strokeWidth={this.props.minified ? 5 : 3}
        strokeDasharray={this.props.minified ? 8 : 4}
      />
    );
  }

  renderSolid() {
    const { solid, layout, minified } = this.props;
    const composite =
      solid.definition.__typename === "CompositeSolidDefinition";

    return (
      <SVGFlowLayoutRect
        {...layout.solid}
        fill={PipelineColorScale(composite ? "solidComposite" : "solid")}
        stroke="#979797"
        strokeWidth={1}
        spacing={0}
        padding={12}
      >
        <SVGMonospaceText
          size={minified ? 30 : 16}
          text={solid.name}
          fill={"#222"}
        />
      </SVGFlowLayoutRect>
    );
  }

  public renderSolidCompositeIndicator() {
    const { x, y, width, height } = this.props.layout.solid;
    return (
      <>
        <rect
          x={x - 6}
          y={y - 6}
          width={width + 12}
          height={height + 12}
          fill={PipelineColorScale("solidComposite")}
          stroke="#979797"
          strokeWidth={1}
        />
        <rect
          x={x - 3}
          y={y - 3}
          width={width + 6}
          height={height + 6}
          fill={PipelineColorScale("solidComposite")}
          stroke="#979797"
          strokeWidth={1}
        />
      </>
    );
  }

  public render() {
    const { solid, layout, dim, selected, minified } = this.props;
    const { metadata } = solid.definition;
    const { x, y, width, height } = layout.solid;

    let configDefinition = null;
    if (solid.definition.__typename === "SolidDefinition") {
      configDefinition = solid.definition.configDefinition;
    }

    const tags: ISolidTag[] = [];

    const kind = metadata.find(m => m.key === "kind");
    const composite =
      solid.definition.__typename === "CompositeSolidDefinition";

    if (kind) {
      tags.push({ label: kind.value, onClick: this.handleKindClicked });
    }
    if (composite) {
      tags.push({ label: "Expand", onClick: this.handleEnterComposite });
    }

    return (
      <g
        onClick={this.handleClick}
        onDoubleClick={this.handleDoubleClick}
        opacity={dim ? 0.3 : 1}
      >
        {selected && this.renderSelectedBox()}
        {composite && this.renderSolidCompositeIndicator()}

        {this.renderSolid()}

        {solid.inputs.map((item, idx) => (
          <SolidIOBox
            {...this.props}
            {...metadataForIO(solid, item)}
            key={idx}
            item={item}
            layout={layout.inputs[item.definition.name].layout}
            colorKey="input"
          />
        ))}

        {solid.outputs.map((item, idx) => (
          <SolidIOBox
            {...this.props}
            {...metadataForIO(solid, item)}
            key={idx}
            item={item}
            layout={layout.outputs[item.definition.name].layout}
            colorKey="output"
          />
        ))}

        {configDefinition && (
          <SolidConfigPort x={x + width - 33} y={y - 13} minified={minified} />
        )}

        {tags.length > 0 && (
          <SolidTags
            x={x}
            y={y + height}
            width={width + 5}
            minified={minified}
            tags={tags}
          />
        )}
      </g>
    );
  }
}
