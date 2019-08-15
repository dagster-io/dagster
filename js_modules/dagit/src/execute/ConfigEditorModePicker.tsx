import * as React from "react";
import { Button, Menu } from "@blueprintjs/core";
import { Select } from "@blueprintjs/select";
import { PipelineDetailsFragment } from "./types/PipelineDetailsFragment";

interface IConfigEditorModePickerProps {
  pipeline: PipelineDetailsFragment;
  modeName: string | null;
  onModeChange: (mode: string) => void;
}

interface Mode {
  name: string;
}

const ModeSelect = Select.ofType<Mode>();

export default class ConfigEditorModePicker extends React.PureComponent<
  IConfigEditorModePickerProps
> {
  getModeFromProps = (props: IConfigEditorModePickerProps) => {
    return props.modeName
      ? props.pipeline.modes.find(m => m.name === props.modeName)
      : props.pipeline.modes[0];
  };

  getCurrentMode = () => {
    return this.getModeFromProps(this.props);
  };

  componentDidMount() {
    const currentMode = this.getCurrentMode();
    if (currentMode) {
      this.props.onModeChange(currentMode.name);
    }
  }

  componentDidUpdate(prevProps: IConfigEditorModePickerProps) {
    const currentMode = this.getCurrentMode();
    const prevMode = this.getModeFromProps(prevProps);

    if (currentMode && currentMode !== prevMode) {
      this.props.onModeChange(currentMode.name);
    }
  }

  render() {
    const singleMode = this.props.pipeline.modes.length === 1;
    const currentMode = this.getCurrentMode();

    return (
      <div>
        <ModeSelect
          activeItem={currentMode}
          filterable={true}
          disabled={singleMode}
          items={this.props.pipeline.modes}
          itemPredicate={(query, mode) =>
            query.length === 0 || mode.name.includes(query)
          }
          itemRenderer={(mode, props) => (
            <Menu.Item
              active={props.modifiers.active}
              key={mode.name}
              text={mode.name}
              onClick={props.handleClick}
            />
          )}
          onItemSelect={this.onItemSelect}
        >
          <Button
            text={currentMode ? "Mode: " + currentMode.name : "Select Mode"}
            disabled={singleMode}
            icon="insert"
            rightIcon="caret-down"
          />
        </ModeSelect>
      </div>
    );
  }

  private onItemSelect = (mode: Mode) => {
    this.props.onModeChange(mode.name);
  };
}
