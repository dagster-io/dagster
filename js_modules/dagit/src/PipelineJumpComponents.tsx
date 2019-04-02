import * as React from "react";
import * as ReactDOM from "react-dom";
import { Select } from "@blueprintjs/select";
import { Button, MenuItem } from "@blueprintjs/core";
import gql from "graphql-tag";
import { PipelineJumpBarFragment } from "./types/PipelineJumpBarFragment";
import { SolidJumpBarFragment_solids } from "./types/SolidJumpBarFragment";

interface IPipelineJumpBarProps {
  pipelines: Array<PipelineJumpBarFragment>;
  selectedPipeline: PipelineJumpBarFragment | undefined;
  onItemSelect: (pipeline: PipelineJumpBarFragment) => void;
}

interface ISolidJumpBarProps {
  solids: Array<SolidJumpBarFragment_solids>;
  selectedSolid: SolidJumpBarFragment_solids | undefined;
  onItemSelect: (solid: SolidJumpBarFragment_solids) => void;
}

class GlobalKeyHandler extends React.Component<{
  onGlobalKeydown: (event: KeyboardEvent) => void;
}> {
  componentDidMount() {
    window.addEventListener("keydown", this.onGlobalKeydown);
  }

  componentWillUnmount() {
    window.removeEventListener("keydown", this.onGlobalKeydown);
  }

  onGlobalKeydown = (event: KeyboardEvent) => {
    const { target } = event;

    if (
      (target && (target as HTMLElement).nodeName === "INPUT") ||
      (target as HTMLElement).nodeName === "TEXTAREA"
    ) {
      return;
    }
    this.props.onGlobalKeydown(event);
  };

  render() {
    return this.props.children;
  }
}

export class SolidJumpBar extends React.Component<ISolidJumpBarProps> {
  static fragments = {
    SolidJumpBarFragment: gql`
      fragment SolidJumpBarFragment on Pipeline {
        solids {
          name
        }
      }
    `
  };

  select: React.RefObject<
    Select<SolidJumpBarFragment_solids>
  > = React.createRef();

  onGlobalKeydown = (event: KeyboardEvent) => {
    if (event.key === "s") {
      activateSelect(this.select.current);
    }
  };

  render() {
    const { solids, selectedSolid, onItemSelect } = this.props;

    return (
      <GlobalKeyHandler onGlobalKeydown={this.onGlobalKeydown}>
        <SolidSelect
          ref={this.select}
          items={solids}
          itemRenderer={BasicNameRenderer}
          itemListPredicate={BasicNamePredicate}
          noResults={<MenuItem disabled={true} text="No results." />}
          onItemSelect={onItemSelect}
        >
          <Button
            text={selectedSolid ? selectedSolid.name : "Select a Solid..."}
            rightIcon="double-caret-vertical"
          />
        </SolidSelect>
      </GlobalKeyHandler>
    );
  }
}

export class PipelineJumpBar extends React.Component<IPipelineJumpBarProps> {
  static fragments = {
    PipelineJumpBarFragment: gql`
      fragment PipelineJumpBarFragment on Pipeline {
        name
      }
    `
  };

  select: React.RefObject<Select<PipelineJumpBarFragment>> = React.createRef();

  onGlobalKeydown = (event: KeyboardEvent) => {
    if (event.key === "p") {
      activateSelect(this.select.current);
    }
    if (this.select.current && this.select.current.state.isOpen) {
      if (event.key === "Escape" && this.props.selectedPipeline) {
        this.props.onItemSelect(this.props.selectedPipeline);
      }
    }
  };

  render() {
    const { pipelines, selectedPipeline, onItemSelect } = this.props;

    return (
      <GlobalKeyHandler onGlobalKeydown={this.onGlobalKeydown}>
        <PipelineSelect
          ref={this.select}
          items={pipelines}
          itemRenderer={BasicNameRenderer}
          itemListPredicate={BasicNamePredicate}
          noResults={<MenuItem disabled={true} text="No results." />}
          onItemSelect={onItemSelect}
        >
          <Button
            text={
              selectedPipeline ? selectedPipeline.name : "Select a Pipeline..."
            }
            rightIcon="double-caret-vertical"
          />
        </PipelineSelect>
      </GlobalKeyHandler>
    );
  }
}

const PipelineSelect = Select.ofType<PipelineJumpBarFragment>();

const SolidSelect = Select.ofType<SolidJumpBarFragment_solids>();

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
