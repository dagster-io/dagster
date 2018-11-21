import * as React from "react";
import {
  Button,
  ButtonGroup,
  MenuItem,
  Dialog,
  FormGroup,
  Label,
  Classes,
  Intent
} from "@blueprintjs/core";
import { Select } from "@blueprintjs/select";

interface IConfigSelectorProps {
  availableConfigs: Array<string>;
  selectedConfig: string | null;
  onCreateConfig: (newConfig: string) => void;
  onSelectConfig: (newConfig: string | null) => void;
  onDeleteConfig: (configName: string) => void;
}

interface IConfigSelectorState {
  isCreateConfigOpen: boolean;
  configName: string;
}

const ConfigSelect = Select.ofType<string>();

export default class ConfigSelector extends React.Component<
  IConfigSelectorProps,
  IConfigSelectorState
> {
  state = {
    isCreateConfigOpen: false,
    configName: ""
  };

  handleOpenDialog = () => {
    this.setState({
      isCreateConfigOpen: true
    });
  };

  handleCloseDialog = () => {
    this.setState({
      isCreateConfigOpen: false,
      configName: ""
    });
  };

  handleCreateConfig = () => {
    if (this.state.configName.length > 0) {
      const configName = this.state.configName;
      this.props.onCreateConfig(configName);
      this.setState({
        isCreateConfigOpen: false,
        configName: ""
      });
    }
  };

  handleChangeConfigName = (e: React.ChangeEvent<HTMLInputElement>) => {
    this.setState({
      configName: e.target.value
    });
  };

  render() {
    return (
      <>
        <ButtonGroup fill={true} large={true}>
          <ConfigSelect
            items={this.props.availableConfigs}
            itemRenderer={(config: string, { handleClick, modifiers }) => {
              return (
                <MenuItem
                  active={modifiers.active}
                  disabled={modifiers.disabled}
                  label={config}
                  text={config}
                  key={config}
                  onClick={handleClick}
                />
              );
            }}
            onItemSelect={this.props.onSelectConfig}
            noResults={<MenuItem disabled={true} text="No configs" />}
            filterable={false}
          >
            {/* children become the popover target; render value here */}
            <Button
              text={this.props.selectedConfig || "Select config..."}
              rightIcon="double-caret-vertical"
            />
          </ConfigSelect>
          <Button
            text="Create new config"
            rightIcon="add"
            onClick={this.handleOpenDialog}
          />
          <Button
            text="Delete config"
            rightIcon="delete"
            disabled={!this.props.selectedConfig}
            onClick={() =>
              this.props.selectedConfig &&
              this.props.onDeleteConfig(this.props.selectedConfig)
            }
          />
        </ButtonGroup>
        <Dialog
          isOpen={this.state.isCreateConfigOpen}
          onClose={this.handleCloseDialog}
          title="Create config"
        >
          <div className={Classes.DIALOG_BODY}>
            <FormGroup>
              <Label>
                Name
                <input
                  className={Classes.INPUT}
                  onChange={this.handleChangeConfigName}
                  value={this.state.configName}
                />
              </Label>
            </FormGroup>
          </div>
          <div className={Classes.DIALOG_FOOTER}>
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <Button onClick={this.handleCloseDialog}>Close</Button>
              <Button
                intent={Intent.PRIMARY}
                disabled={this.state.configName.length === 0}
                onClick={this.handleCreateConfig}
              >
                Create config
              </Button>
            </div>
          </div>
        </Dialog>
      </>
    );
  }
}
