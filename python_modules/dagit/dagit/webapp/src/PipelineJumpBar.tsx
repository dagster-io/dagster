import * as React from "react";
import * as ReactDOM from "react-dom";
import { Select } from "@blueprintjs/select";
import { Button, MenuItem } from "@blueprintjs/core";
import styled from "styled-components";
import { History } from "history";
import gql from "graphql-tag";
import PipelineExplorer from "./PipelineExplorer";
import {
  PipelineJumpBarFragment,
  PipelineJumpBarFragment_solids
} from "./types/PipelineJumpBarFragment";

interface IPipelinesProps {
  history: History;
  pipelines: Array<PipelineJumpBarFragment>;
  selectedPipeline: PipelineJumpBarFragment | undefined;
  selectedSolid: PipelineJumpBarFragment_solids | undefined;
}

export default class PipelineJumpBar extends React.Component<
  IPipelinesProps,
  {}
> {
  static fragments = {
    PipelineJumpBarFragment: gql`
      fragment PipelineJumpBarFragment on Pipeline {
        name
        solids {
          name
        }
      }
    `
  };

  solidSelect: React.RefObject<
    Select<PipelineJumpBarFragment_solids>
  > = React.createRef();

  pipelineSelect: React.RefObject<
    Select<PipelineJumpBarFragment>
  > = React.createRef();

  componentDidMount() {
    window.addEventListener("keydown", this.onGlobalKeydown);
  }

  componentWillUnmount() {
    window.removeEventListener("keydown", this.onGlobalKeydown);
  }

  onGlobalKeydown = (event: KeyboardEvent) => {
    const { history, selectedPipeline } = this.props;
    const { key, target } = event;

    if (
      (target && (target as HTMLElement).nodeName === "INPUT") ||
      (target as HTMLElement).nodeName === "TEXTAREA"
    ) {
      return;
    }
    if (key === "s") {
      activateSelect(this.solidSelect.current);
    }
    if (key === "p") {
      activateSelect(this.pipelineSelect.current);
    }
    if (key === "Escape" && selectedPipeline) {
      history.push(`/${selectedPipeline.name}`);
    }
  };

  onSelectPipeline = (pipeline: PipelineJumpBarFragment) => {
    this.props.history.push(`/${pipeline.name}`);
  };

  onSelectSolid = (solid: PipelineJumpBarFragment_solids) => {
    const { history, selectedPipeline } = this.props;

    if (selectedPipeline) {
      history.push(`/${selectedPipeline.name}/${solid.name}`);
    }
  };

  render() {
    const { pipelines, selectedPipeline, selectedSolid } = this.props;

    return (
      <PipelinesJumpBarWrapper>
        <PipelineSelect
          ref={this.pipelineSelect}
          items={pipelines}
          itemRenderer={BasicNameRenderer}
          itemListPredicate={BasicNamePredicate}
          noResults={<MenuItem disabled={true} text="No results." />}
          onItemSelect={this.onSelectPipeline}
        >
          <Button
            text={
              selectedPipeline ? selectedPipeline.name : "Select a Pipeline..."
            }
            rightIcon="double-caret-vertical"
          />
        </PipelineSelect>
        <SelectDivider>/</SelectDivider>
        {selectedPipeline && (
          <SolidSelect
            ref={this.solidSelect}
            items={selectedPipeline.solids}
            itemRenderer={BasicNameRenderer}
            itemListPredicate={BasicNamePredicate}
            noResults={<MenuItem disabled={true} text="No results." />}
            onItemSelect={this.onSelectSolid}
          >
            <Button
              text={selectedSolid ? selectedSolid.name : "Select a Solid..."}
              rightIcon="double-caret-vertical"
            />
          </SolidSelect>
        )}
      </PipelinesJumpBarWrapper>
    );
  }
}

const PipelinesJumpBarWrapper = styled.div`
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

const PipelineSelect = Select.ofType<PipelineJumpBarFragment>();
const SolidSelect = Select.ofType<PipelineJumpBarFragment_solids>();

const BasicNamePredicate = (text: string, items: any) =>
  items
    .filter((i: any) => i.name.toLowerCase().includes(text.toLowerCase()))
    .slice(0, 20);

const BasicNameRenderer = (
  item: { name: string },
  options: { handleClick: any; modifiers: any }
) => (
  <MenuItem
    key={item.name}
    text={item.name}
    active={options.modifiers.active}
    onClick={options.handleClick}
  />
);

function activateSelect(select: Select<any> | null) {
  if (!select) return;
  const selectEl = ReactDOM.findDOMNode(select) as HTMLElement;
  const btnEl = selectEl.querySelector("button");
  if (btnEl) {
    btnEl.click();
  }
}
