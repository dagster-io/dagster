import * as React from "react";
import styled from "styled-components";
import ConfigCodeEditor from "./ConfigCodeEditor";
import ConfigSelector from "./ConfigSelector";
import { ValidationResult, TypeConfig } from "./codemirror-yaml/mode";

interface IConfigEditorProps {
  availableConfigs: Array<string>;
  selectedConfig: string | null;
  configCode: string | null;
  typeConfig: TypeConfig;
  onCheckConfig: (newConfig: any) => Promise<ValidationResult>;
  onCreateConfig: (newConfig: string) => void;
  onChangeConfig: (newValue: string) => void;
  onSelectConfig: (newConfig: string | null) => void;
  onDeleteConfig: (configName: string) => void;
}

export default class ConfigEditor extends React.Component<
  IConfigEditorProps,
  {}
> {
  renderCodeEditor() {
    if (this.props.selectedConfig && this.props.configCode) {
      return (
        <ConfigCodeEditor
          typeConfig={this.props.typeConfig}
          configCode={this.props.configCode}
          onCheckConfig={this.props.onCheckConfig}
          onChangeConfig={this.props.onChangeConfig}
        />
      );
    } else {
      return null;
    }
  }

  render() {
    return (
      <>
        <ConfigSelectorWrapper>
          <ConfigSelector
            availableConfigs={this.props.availableConfigs}
            selectedConfig={this.props.selectedConfig}
            onCreateConfig={this.props.onCreateConfig}
            onSelectConfig={this.props.onSelectConfig}
            onDeleteConfig={this.props.onDeleteConfig}
          />
        </ConfigSelectorWrapper>
        {this.renderCodeEditor()}
      </>
    );
  }
}

const ConfigSelectorWrapper = styled.div`
  margin-top: 5px;
  margin-bottom: 5px;
`;
