import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Card, H5, Code, Colors } from "@blueprintjs/core";
import PipelineColorScale from "./PipelineColorScale";
import { SolidNodeFragment } from "./types/SolidNodeFragment";
import { IFullSolidLayout } from "./getFullSolidLayout";

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
      const {
        layout: { x, y, width, height }
      } = this.props.layout.inputs[input.name];

      return (
        <foreignObject
          key={i}
          x={x - this.props.layout.solid.x}
          y={y - this.props.layout.solid.y}
          width={width}
          height={height}
        >
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
    const {
      layout: { x, y, width, height }
    } = this.props.layout.output;

    return (
      <foreignObject
        x={x - this.props.layout.solid.x}
        y={y - this.props.layout.solid.y}
        width={width}
        height={height}
      >
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
      const width =
        this.props.layout.solid.width +
        this.props.layout.output.layout.width * 2 +
        20;
      const height = this.props.layout.solid.height + 20;
      return (
        <rect
          x={-10 - this.props.layout.output.layout.width}
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
    return (
      <g
        onClick={this.handleClick}
        transform={`translate(${this.props.layout.solid.x}, ${
          this.props.layout.solid.y
        })`}
      >
        {this.renderSelectedBox()}
        <foreignObject
          width={this.props.layout.solid.width}
          height={this.props.layout.solid.height}
        >
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
