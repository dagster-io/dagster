import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import PipelineColorScale from "./PipelineColorScale";
import { SolidNodeFragment } from "./types/SolidNodeFragment";
import { IFullSolidLayout } from "./getFullSolidLayout";
import { TypeName } from "../TypeWithTooltip";

interface ISolidNodeProps {
  layout: IFullSolidLayout;
  solid: SolidNodeFragment;
  selected?: boolean;
  onClick?: (solid: any) => void;
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
    if (this.props.onClick) {
      this.props.onClick(this.props.solid.name);
    }
  };

  renderInputs() {
    return Object.keys(this.props.layout.inputs).map((key, i) => {
      const { x, y, width, height } = this.props.layout.inputs[key].layout;

      const input = this.props.solid.inputs.find(
        o => o.definition.name === key
      );
      return (
        <foreignObject key={i} x={x} y={y} height={height}>
          <InputContainer>
            <Port filled={true} />
            {width == 0 && (
              <InputOutputName>{input!.definition.name}</InputOutputName>
            )}
            {width == 0 && <TypeName>{input!.definition.type.name}</TypeName>}
          </InputContainer>
        </foreignObject>
      );
    });
  }

  renderOutputs() {
    return Object.keys(this.props.layout.outputs).map((key, i) => {
      const { x, y, width, height } = this.props.layout.outputs[key].layout;
      const output = this.props.solid.outputs.find(
        o => o.definition.name === key
      );

      return (
        <foreignObject key={i} x={x} y={y} height={height}>
          <OutputContainer>
            <Port filled={true} />
            {width == 0 && (
              <InputOutputName>{output!.definition.name}</InputOutputName>
            )}
            {width == 0 && <TypeName>{output!.definition.type.name}</TypeName>}
          </OutputContainer>
        </foreignObject>
      );
    });
  }

  renderSelectedBox() {
    if (this.props.selected) {
      const { x, y, width, height } = this.props.layout.boundingBox;
      return (
        <rect
          x={x - 10}
          y={y - 10}
          width={width + 20}
          height={height + 20}
          fill="transparent"
          stroke={Colors.GRAY3}
          strokeWidth="1"
          strokeDasharray="4"
        />
      );
    } else {
      return null;
    }
  }

  public renderSolid() {
    return (
      <foreignObject {...this.props.layout.solid}>
        <SolidContainer>
          <SolidName>{this.props.solid.name}</SolidName>
        </SolidContainer>
      </foreignObject>
    );
  }
  public render() {
    return (
      <g onClick={this.handleClick}>
        {this.renderSelectedBox()}
        {this.renderSolid()}
        {this.renderInputs()}
        {this.renderOutputs()}
      </g>
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

const SolidName = styled.div`
  font-family: "Source Code Pro", monospace;
  font-weight: 500;
  font-size: 18px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const IOContainer = styled.div`
  padding: 7px;
  height: 100%;
  position: absolute;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
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
