import * as React from "react";
import * as ReactDOM from "react-dom";
import gql from "graphql-tag";
import styled from "styled-components";
import { History } from "history";
import Pipeline from "./Pipeline";
import { PipelinesFragment } from "./types/PipelinesFragment";
import { Select } from "@blueprintjs/select";
import { Button, MenuItem } from "@blueprintjs/core";
import {
  PipelineFragment,
  PipelineFragment_solids
} from "./types/PipelineFragment";

interface IPipelinesProps {
  history: History;
  pipelines: Array<PipelinesFragment>;
  selectedPipeline: string;
  selectedSolid: string;
}

const PipelineSelect = Select.ofType<PipelinesFragment>();
const SolidSelect = Select.ofType<PipelineFragment_solids>();

export default class PipelinesNav extends React.Component<IPipelinesProps, {}> {
  static fragments = {
    PipelinesFragment: gql`
      fragment PipelinesFragment on Pipeline {
        ...PipelineFragment
      }

      ${Pipeline.fragments.PipelineFragment}
    `
  };

  solidSelect: React.RefObject<
    Select<PipelineFragment_solids>
  > = React.createRef();

  pipelineSelect: React.RefObject<
    Select<PipelinesFragment>
  > = React.createRef();

  componentDidMount() {
    window.addEventListener("keydown", this.onGlobalKeydown);
  }

  componentWillUnmount() {
    window.removeEventListener("keydown", this.onGlobalKeydown);
  }

  onGlobalKeydown = (event: KeyboardEvent) => {
    if (event.target && (event.target as HTMLElement).nodeName === "INPUT") {
      return;
    }
    if (event.key === "s") {
      const el = (ReactDOM.findDOMNode(
        this.solidSelect.current!
      ) as HTMLElement).querySelector("button")!;
      el.click();
    }
    if (event.key === "p") {
      const el = (ReactDOM.findDOMNode(
        this.pipelineSelect.current!
      ) as HTMLElement).querySelector("button")!;
      el.click();
    }
    if (event.key === "Escape") {
      this.props.history.push(`/${this.props.selectedPipeline}`);
    }
  };

  onSelectPipeline = (pipeline: PipelineFragment) => {
    this.props.history.push(`/${pipeline.name}`);
  };

  onSelectSolid = (solid: PipelineFragment_solids) => {
    this.props.history.push(`/${this.props.selectedPipeline}/${solid.name}`);
  };

  render() {
    const selectedPipeline = this.props.pipelines.find(
      ({ name }) => name === this.props.selectedPipeline
    );

    return (
      <PipelinesNavWrapper>
        <PipelineSelect
          ref={this.pipelineSelect}
          items={this.props.pipelines}
          itemListPredicate={(text, items) =>
            items.filter(i => i.name.startsWith(text)).slice(0, 20)
          }
          itemRenderer={(pipeline, { handleClick, modifiers }) => (
            <MenuItem
              active={modifiers.active}
              key={pipeline.name}
              text={pipeline.name}
              onClick={handleClick}
            />
          )}
          noResults={<MenuItem disabled={true} text="No results." />}
          onItemSelect={this.onSelectPipeline}
        >
          <Button
            text={this.props.selectedPipeline || "Select a Pipeline..."}
            rightIcon="double-caret-vertical"
          />
        </PipelineSelect>
        <SelectDivider>/</SelectDivider>
        {selectedPipeline && (
          <SolidSelect
            ref={this.solidSelect}
            items={selectedPipeline.solids}
            itemListPredicate={(text, items) =>
              items.filter(i => i.name.startsWith(text)).slice(0, 20)
            }
            itemRenderer={(solid, { handleClick, modifiers }) => (
              <MenuItem
                active={modifiers.active}
                key={solid.name}
                text={solid.name}
                onClick={handleClick}
              />
            )}
            noResults={<MenuItem disabled={true} text="No results." />}
            onItemSelect={this.onSelectSolid}
          >
            <Button
              text={this.props.selectedSolid || "Select a Solid..."}
              rightIcon="double-caret-vertical"
            />
          </SolidSelect>
        )}
      </PipelinesNavWrapper>
    );
  }
}

const BreadcrumbText = styled.h2`
  font-family: "Source Code Pro", monospace;
  font-weight: 500;
`;

const PipelinesNavWrapper = styled.div`
  display: flex;
  align-items: center;
`;
const SelectDivider = styled.div`
  padding: 0 10px;
  font-size: 24px;
  line-height: 24px;
  color: rgba(16, 22, 26, 0.15);
  display: inline-block;
`;
