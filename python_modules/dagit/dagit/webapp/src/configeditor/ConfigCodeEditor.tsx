import * as React from "react";
import { Controlled as CodeMirror } from "react-codemirror2";
import { injectGlobal } from "styled-components";
import "codemirror/mode/yaml/yaml";
import "codemirror/lib/codemirror.css";
import "codemirror/theme/material.css";

export default class ConfigCodeEditor extends React.Component {
  state = {
    code:
      "// This is config editor. Paste or write config here to have it validated"
  };

  render() {
    return (
      <CodeMirror
        value={this.state.code}
        options={{
          mode: "yaml",
          theme: "material",
          lineNumbers: true,
          indentUnit: 1,
          tabSize: 2,
          smartIndent: true
        }}
        onBeforeChange={(editor, data, value) => {
          this.setState({ code: value });
        }}
      />
    );
  }
}

injectGlobal`
  .react-codemirror2, .CodeMirror {
    && {
      height: 100%;
    }
  }
`;
