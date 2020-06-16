import * as React from "react";
import * as ReactDOM from "react-dom";
import { Select } from "@blueprintjs/select";
import { Button, MenuItem } from "@blueprintjs/core";
import gql from "graphql-tag";
import { SolidJumpBarFragment_solids } from "./types/SolidJumpBarFragment";
import { ShortcutHandler } from "./ShortcutHandler";
import { DagsterRepositoryContext } from "./DagsterRepositoryContext";
import styled from "styled-components/macro";

interface PipelineJumpBarProps {
  selectedPipelineName: string | undefined;
  onChange: (pipelineName: string) => void;
}

interface SolidJumpBarProps {
  solids: Array<SolidJumpBarFragment_solids>;
  selectedSolid: SolidJumpBarFragment_solids | undefined;
  onChange: (solid: SolidJumpBarFragment_solids) => void;
}

export class SolidJumpBar extends React.Component<SolidJumpBarProps> {
  static fragments = {
    SolidJumpBarFragment: gql`
      fragment SolidJumpBarFragment on IPipelineSnapshot {
        solids {
          name
        }
      }
    `
  };

  select: React.RefObject<Select<string>> = React.createRef();

  render() {
    const { solids, selectedSolid, onChange } = this.props;

    return (
      <ShortcutHandler
        onShortcut={() => activateSelect(this.select.current)}
        shortcutLabel={`⌥S`}
        shortcutFilter={e => e.keyCode === 83 && e.altKey}
      >
        <StringSelectNoIntrinsicWidth
          ref={this.select}
          items={solids.map(s => s.name)}
          itemRenderer={BasicStringRenderer}
          itemListPredicate={BasicStringPredicate}
          noResults={<MenuItem disabled={true} text="No results." />}
          onItemSelect={name => onChange(solids.find(s => s.name === name)!)}
        >
          <Button
            text={selectedSolid ? selectedSolid.name : "Select a Solid..."}
            rightIcon="double-caret-vertical"
          />
        </StringSelectNoIntrinsicWidth>
      </ShortcutHandler>
    );
  }
}

export class PipelineJumpBar extends React.Component<PipelineJumpBarProps> {
  select: React.RefObject<Select<string>> = React.createRef();

  onGlobalKeyDown = (event: KeyboardEvent) => {
    if (event.keyCode === 80 && event.altKey) {
      // Opt-P
      activateSelect(this.select.current);
      event.preventDefault();
    }
    if (this.select.current && this.select.current.state.isOpen) {
      if (event.key === "Escape" && this.props.selectedPipelineName) {
        this.props.onChange(this.props.selectedPipelineName);
      }
    }
  };

  render() {
    const { onChange, selectedPipelineName } = this.props;

    return (
      <ShortcutHandler
        onGlobalKeyDown={this.onGlobalKeyDown}
        shortcutLabel={`⌥P`}
      >
        <DagsterRepositoryContext.Consumer>
          {context => (
            <StringSelectNoIntrinsicWidth
              ref={this.select}
              items={context.repository?.pipelines.map(x => x.name) || []}
              itemRenderer={BasicStringRenderer}
              itemListPredicate={BasicStringPredicate}
              noResults={<MenuItem disabled={true} text="No results." />}
              onItemSelect={onChange}
            >
              <Button
                text={selectedPipelineName || "Select a pipeline..."}
                id="playground-select-pipeline"
                disabled={!context.repository?.pipelines.length}
                rightIcon="double-caret-vertical"
                icon="send-to-graph"
              />
            </StringSelectNoIntrinsicWidth>
          )}
        </DagsterRepositoryContext.Consumer>
      </ShortcutHandler>
    );
  }
}

// By default, Blueprint's Select component has an intrinsic size determined by the length of
// it's content, which in our case can be wildly long and unruly. Giving the Select a min-width
// of 0px and adding "width" rules to all nested <divs> that are a function of the parent (eg: 100%)
// tells the layout engine that this can be assigned a width by it's container. This allows
// us to make the Select "as wide as the layout allows" and have it truncate first.
//
const StringSelectNoIntrinsicWidth = styled(Select.ofType<string>())`
  min-width: 0;

  & .bp3-popover-target {
    width: 100%;
  }
  & .bp3-button {
    max-width: 100%;
  }
  & .bp3-button-text {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
  }
`;

const BasicStringPredicate = (text: string, items: string[]) =>
  items.filter(i => i.toLowerCase().includes(text.toLowerCase())).slice(0, 20);

const BasicStringRenderer = (
  item: string,
  options: { handleClick: any; modifiers: any }
) => (
  <MenuItem
    key={item}
    text={item}
    active={options.modifiers.active}
    onClick={options.handleClick}
  />
);

function activateSelect(select: Select<any> | null) {
  if (!select) return;
  // eslint-disable-next-line react/no-find-dom-node
  const selectEl = ReactDOM.findDOMNode(select) as HTMLElement;
  const btnEl = selectEl.querySelector("button");
  if (btnEl) {
    btnEl.click();
  }
}
