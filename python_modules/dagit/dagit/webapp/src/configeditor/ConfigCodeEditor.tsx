import * as React from "react";
import { injectGlobal } from "styled-components";
import debounce from "lodash.debounce";
import * as CodeMirror from "codemirror";
import "codemirror/lib/codemirror.css";
import "codemirror/theme/material.css";
import "codemirror/addon/hint/show-hint";
import "codemirror/addon/hint/show-hint.css";
import "codemirror/addon/comment/comment";
import "codemirror/addon/fold/foldgutter";
import "codemirror/addon/fold/foldgutter.css";
import "codemirror/addon/fold/indent-fold";
import "codemirror/addon/search/search";
import "codemirror/addon/search/searchcursor";
import "codemirror/addon/search/jump-to-line";
import "codemirror/addon/dialog/dialog";
import "codemirror/addon/lint/lint";
import "codemirror/addon/lint/lint.css";
import "codemirror/keymap/sublime";
import { Controlled as CodeMirrorReact } from "react-codemirror2";
import "./codemirror-yaml/mode";
import {
  TypeConfig as YamlModeTypeConfig,
  LintJson as YamlModeLintJson
} from "./codemirror-yaml/mode";

interface IConfigEditorProps {
  typeConfig: YamlModeTypeConfig;
  lintJson: YamlModeLintJson;
}

interface IConfigEditorState {
  code: string;
}

const AUTO_COMPLETE_AFTER_KEY = /^[a-zA-Z0-9_@(]$/;

export default class ConfigCodeEditor extends React.Component<
  IConfigEditorProps,
  IConfigEditorState
> {
  state = {
    code: "# This is config editor\n\n"
  };

  render() {
    const performLint = debounce((editor: any) => editor.performLint(), 3000);
    return (
      <CodeMirrorReact
        value={this.state.code}
        options={
          {
            mode: "yaml",
            theme: "material",
            lineNumbers: true,
            indentUnit: 2,
            smartIndent: true,
            showCursorWhenSelecting: true,
            lint: {
              lintJson: this.props.lintJson,
              lintOnChange: false
            },
            hintOptions: {
              completeSingle: false,
              closeOnUnfocus: false,
              typeConfig: this.props.typeConfig
            },
            extraKeys: {
              "Cmd-Space": (editor: any) =>
                editor.showHint({
                  completeSingle: true
                }),
              "Ctrl-Space": (editor: any) =>
                editor.showHint({
                  completeSingle: true
                }),
              "Alt-Space": (editor: any) =>
                editor.showHint({
                  completeSingle: true
                }),
              "Shift-Space": (editor: any) =>
                editor.showHint({
                  completeSingle: true
                }),
              "Shift-Tab": (editor: any) => editor.execCommand("indentLess"),
              Tab: (editor: any) => editor.execCommand("indentMore"),
              // Persistent search box in Query Editor
              "Cmd-F": "findPersistent",
              "Ctrl-F": "findPersistent"
            },
            gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
            foldGutter: true
          } as any
        }
        onBeforeChange={(editor, data, value) => {
          this.setState({ code: value });
        }}
        onChange={(editor: any) => {
          performLint(editor);
        }}
        onBlur={(editor: any) => {
          performLint(editor);
        }}
        onKeyUp={(editor, event: KeyboardEvent) => {
          if (AUTO_COMPLETE_AFTER_KEY.test(event.key)) {
            editor.execCommand("autocomplete");
          }
        }}
      />
    );
  }
}

injectGlobal`
  .react-codemirror2, .CodeMirror {
    && {
      height: 100%;
      width: 100%;
    }
  }

  .CodeMirror-linenumber {

  }
`;
