import * as React from "react";
import gql from "graphql-tag";
import styled, { StyledComponentClass } from "styled-components";
import { Colors } from "@blueprintjs/core";
import PipelineColorScale from "./PipelineColorScale";
import {
  SolidNodeFragment,
  SolidNodeFragment_inputs,
  SolidNodeFragment_outputs
} from "./types/SolidNodeFragment";
import { IFullSolidLayout, ILayout } from "./getFullSolidLayout";
import { TypeName } from "../TypeWithTooltip";

interface ISolidNodeProps {
  layout: IFullSolidLayout;
  solid: SolidNodeFragment;
  minified: boolean;
  selected: boolean;
  dim: boolean;
  onClick?: (solid: string) => void;
  onDoubleClick?: (solid: string) => void;
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
    ComponentClass: StyledComponentClass<any, any, any>,
    items: Array<SolidNodeFragment_inputs | SolidNodeFragment_outputs>,
    layout: { [inputName: string]: { layout: ILayout } }
  ) {
    const root = this.props.layout.solid;

    return Object.keys(layout).map((key, i) => {
      const { x, y, width, height } = layout[key].layout;
      const input = items.find(o => o.definition.name === key);

      return (
        <ComponentClass
          key={i}
          style={{ left: x - root.x, top: y - root.y, height: height }}
        >
          <Port filled={true} />
          {width == 0 &&
            !this.props.minified && (
              <InputOutputName>{input!.definition.name}:</InputOutputName>
            )}
          {width == 0 &&
            !this.props.minified && (
              <TypeName>{input!.definition.type.name}</TypeName>
            )}
        </ComponentClass>
      );
    });
  }

  renderSelectedBox() {
    if (!this.props.selected) {
      return null;
    }
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
      <SolidContainer>
        <SolidName fontSize={this.props.minified ? 30 : 18}>
          {this.props.solid.name}
        </SolidName>
      </SolidContainer>
    );
  }

  public render() {
    const { solid, layout } = this.props;

    return (
      <>
        {this.renderSelectedBox()}
        <foreignObject
          {...this.props.layout.solid}
          onClick={this.handleClick}
          onDoubleClick={this.handleDoubleClick}
          style={{ opacity: this.props.dim ? 0.3 : 1 }}
        >
          {this.renderSolid()}
          {this.renderIO(InputContainer, solid.inputs, layout.inputs)}
          {this.renderIO(OutputContainer, solid.outputs, layout.outputs)}
        </foreignObject>
      </>
    );
  }
}

const SolidContainer = styled.div`
  padding: 12px;
  border: 1px solid #979797;
  background-color: ${PipelineColorScale("solid")};
  height: 100%;
  margin-top: 0;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
`;

const SolidName = styled.div<{ fontSize: number }>`
  font-family: "Source Code Pro", monospace;
  font-weight: 500;
  font-size: ${props => props.fontSize}px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const IOContainer = styled.div`
  padding: 7px;
  position: absolute;
  display: flex;
  align-items: center;
`;

const InputContainer = styled(IOContainer)`
  border: 1px solid #979797;
  background-color: ${PipelineColorScale("input")};
`;

const OutputContainer = styled(IOContainer)`
  border: 1px solid #979797;
  background-color: ${PipelineColorScale("output")};
`;

const InputOutputName = styled.div`
  font-family: "Source Code Pro", monospace;
  font-size: 15px;
  color: white;
  overflow: hidden;
  padding-left: 7px;
  text-overflow: ellipsis;
  padding-right: 12px;
  white-space: nowrap;
  max-width: 300px;
`;

const Port = styled.div<{ filled: boolean }>`
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 7px;
  border: 2px solid rgba(255, 255, 255, 0.7);
  background: ${props =>
    props.filled ? "rgba(0, 0, 0, 0.3)" : "rgba(255, 255, 255, 0.3)"};
`;
