import * as React from "react";
import { Button, Intent, Menu } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { Select } from "@blueprintjs/select";
import { PipelineDetailsFragment_modes } from "./types/PipelineDetailsFragment";
import { ModeNotFoundError } from "./ExecutionSessionContainer";

interface ConfigEditorModePickerProps {
  modes: PipelineDetailsFragment_modes[];
  modeError?: ModeNotFoundError;
  modeName: string | null;
  onModeChange: (mode: string) => void;
}

interface Mode {
  name: string;
}

const ModeSelect = Select.ofType<Mode>();

export class ConfigEditorModePicker extends React.PureComponent<
  ConfigEditorModePickerProps
> {
  getModeFromProps = (props: ConfigEditorModePickerProps) => {
    return props.modeName
      ? props.modes.find(m => m.name === props.modeName)
      : props.modes[0];
  };

  getCurrentMode = () => {
    return this.getModeFromProps(this.props);
  };

  componentDidMount() {
    const currentMode = this.getCurrentMode();
    if (currentMode) {
      this.props.onModeChange && this.props.onModeChange(currentMode.name);
    }
  }

  componentDidUpdate(prevProps: ConfigEditorModePickerProps) {
    const currentMode = this.getCurrentMode();
    const prevMode = this.getModeFromProps(prevProps);

    if (currentMode && currentMode !== prevMode) {
      this.props.onModeChange && this.props.onModeChange(currentMode.name);
    }
  }

  render() {
    const singleMode = this.props.modes.length === 1;
    const currentMode = this.getCurrentMode();
    const valid = !this.props.modeError;

    return (
      <ModeSelect
        activeItem={currentMode}
        filterable={true}
        disabled={singleMode && valid}
        items={this.props.modes}
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
          icon={valid ? "insert" : IconNames.WARNING_SIGN}
          intent={valid ? Intent.NONE : Intent.WARNING}
          title="mode-picker-button"
          text={
            valid
              ? currentMode
                ? `Mode: ${currentMode.name}`
                : "Select Mode"
              : "Invalid Mode Selection"
          }
          disabled={singleMode && valid}
          rightIcon="caret-down"
        />
      </ModeSelect>
    );
  }

  private onItemSelect = (mode: Mode) => {
    this.props.onModeChange && this.props.onModeChange(mode.name);
  };
}
