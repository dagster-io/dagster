import * as React from "react";
import gql from "graphql-tag";
import { H5, H6, Text, UL, Code, Collapse } from "@blueprintjs/core";
import SpacedCard from "./SpacedCard";
import { SourceFragment } from "./types/SourceFragment";
import { MaterializationFragment } from "./types/MaterializationFragment";
import { PipelineContextFragment } from "./types/PipelineContextFragment";

interface IArgumentedProps {
  // XXX(freiksenet): Fix
  item: SourceFragment & MaterializationFragment & PipelineContextFragment;
  renderCard?: (props: any) => React.ReactNode;
}

interface IArgumentedState {
  isOpen: boolean;
}

export default class Argumented extends React.Component<
  IArgumentedProps,
  IArgumentedState
> {
  static fragments = {
    SourceFragment: gql`
      fragment SourceFragment on Source {
        name: sourceType
        description
        arguments {
          name
          description
          type
          isOptional
        }
      }
    `,
    MaterializationFragment: gql`
      fragment MaterializationFragment on Materialization {
        name
        description
        arguments {
          name
          description
          type
          isOptional
        }
      }
    `,
    PipelineContextFragment: gql`
      fragment PipelineContextFragment on PipelineContext {
        name
        description
        arguments {
          name
          description
          type
          isOptional
        }
      }
    `
  };

  constructor(props: IArgumentedProps) {
    super(props);
    this.state = {
      isOpen: false
    };
  }

  toggleOpen = () => {
    this.setState(({ isOpen }) => ({
      isOpen: !isOpen
    }));
  };

  public render() {
    const renderCard =
      this.props.renderCard || ((props: any) => <SpacedCard {...props} />);
    return renderCard({
      elevation: 2,
      interactive: true,
      onClick: this.toggleOpen,
      children: (
        <>
          <H5>
            <Code>{this.props.item.name}</Code>
          </H5>{" "}
          <Collapse isOpen={this.state.isOpen}>
            <Text>{this.props.item.description}</Text>
            <H6>Arguments</H6>
            <UL>
              {this.props.item.arguments.map((argument: any, i: number) => (
                <li key={i}>
                  {argument.name} - {argument.isOptional ? "(optional)" : null}{" "}
                  {argument.type}
                </li>
              ))}
            </UL>
          </Collapse>
        </>
      )
    });
  }
}
