import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Card, H5, Code, Colors } from "@blueprintjs/core";
import PipelineColorScale from "./PipelineColorScale";
import { SolidNodeFragment } from "./types/SolidNodeFragment";

interface ISolidNodeProps {
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
          name
          type {
            name
          }
          sources {
            name: sourceType
          }
          dependsOn {
            name
          }
        }
        output {
          type {
            name
          }
          materializations {
            name
          }
          expectations {
            name
            description
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
    return this.props.solid.inputs.map((input, i) => {
      const x = -190;
      const y = 20 + i * 100;
      const height = 80;
      const width = 200;

      return (
        <foreignObject key={i} x={x} y={y} width={width} height={height}>
          <Card
            elevation={3}
            style={{
              backgroundColor: PipelineColorScale("input"),
              height: "100%"
            }}
          >
            <H5>
              <Code>{input.name}</Code> ({input.type.name})
            </H5>
          </Card>
        </foreignObject>
      );
    });
  }

  renderOutput() {
    const x = 250 - 10;
    const y = 20;
    const height = 80;
    const width = 200;

    return (
      <foreignObject x={x} y={y} width={width} height={height}>
        <Card
          elevation={3}
          style={{
            backgroundColor: PipelineColorScale("output"),
            height: "100%"
          }}
        >
          <H5>({this.props.solid.output.type.name})</H5>
        </Card>
      </foreignObject>
    );
  }

  renderSelectedBox() {
    if (this.props.selected) {
      const width = 250 + 200 + 200 + 20;
      const height = this.props.solid.inputs.length * 80 + 60 + 20;
      return (
        <rect
          x={-10 - 200}
          y={-10}
          height={height}
          width={width}
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

  public render() {
    const width = 250;
    const height = this.props.solid.inputs.length * 80 + 60;
    return (
      <g onClick={this.handleClick}>
        {this.renderSelectedBox()}
        <foreignObject width={width} height={height}>
          <Card
            elevation={2}
            style={{
              backgroundColor: PipelineColorScale("solid"),
              height: "100%"
            }}
          >
            <H5>
              <Code>{this.props.solid.name}</Code>
            </H5>
          </Card>
        </foreignObject>
        {this.renderInputs()}
        {this.renderOutput()}
      </g>
    );
  }
}
