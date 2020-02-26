import * as React from "react";
import * as ReactDOM from "react-dom";
import { Select } from "@blueprintjs/select";
import { Button, MenuItem } from "@blueprintjs/core";
import gql from "graphql-tag";
import { SolidJumpBarFragment_solids } from "./types/SolidJumpBarFragment";
import { PipelineNamesContext } from "./PipelineNamesContext";
import { ShortcutHandler } from "./ShortcutHandler";

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
      fragment SolidJumpBarFragment on Pipeline {
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
        <StringSelect
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
        </StringSelect>
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
        <PipelineNamesContext.Consumer>
          {pipelineNames => (
            <StringSelect
              ref={this.select}
              items={pipelineNames}
              itemRenderer={BasicStringRenderer}
              itemListPredicate={BasicStringPredicate}
              noResults={<MenuItem disabled={true} text="No results." />}
              onItemSelect={onChange}
            >
              <Button
                text={selectedPipelineName || "Select a pipeline..."}
                id="playground-select-pipeline"
                disabled={pipelineNames.length === 0}
                rightIcon="double-caret-vertical"
                icon="send-to-graph"
              />
            </StringSelect>
          )}
        </PipelineNamesContext.Consumer>
      </ShortcutHandler>
    );
  }
}

const StringSelect = Select.ofType<string>();

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
