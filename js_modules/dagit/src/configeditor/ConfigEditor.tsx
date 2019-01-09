import * as React from "react";
import { injectGlobal } from "styled-components";
import "codemirror";
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
import "./codemirror-yaml/lint"; // Patch lint
import "codemirror/addon/lint/lint.css";
import "codemirror/keymap/sublime";
import { Controlled as CodeMirrorReact } from "react-codemirror2";
import "./codemirror-yaml/mode";
import {
  TypeConfig as YamlModeTypeConfig,
  LintJson as YamlModeLintJson
} from "./codemirror-yaml/mode";
import { debounce } from "../Util";

interface IConfigEditorProps {
  typeConfig: YamlModeTypeConfig;
  checkConfig: YamlModeLintJson;
  configCode: string;
  onConfigChange: (newValue: string) => void;
}

const AUTO_COMPLETE_AFTER_KEY = /^[a-zA-Z0-9_@(]$/;
const performLint = debounce((editor: any) => {
  editor.performLint();
}, 1000);

export default class ConfigEditor extends React.Component<IConfigEditorProps> {
  render() {
    return (
      <CodeMirrorReact
        value={this.props.configCode}
        options={
          {
            mode: "yaml",
            theme: "material",
            lineNumbers: true,
            indentUnit: 2,
            smartIndent: true,
            showCursorWhenSelecting: true,
            lintOnChange: false,
            lint: {
              checkConfig: this.props.checkConfig,
              lintOnChange: false,
              onUpdateLinting: false
            },
            hintOptions: {
              completeSingle: false,
              closeOnUnfocus: false,
              typeConfig: this.props.typeConfig
            },
            keyMap: "sublime",
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
            gutters: [
              "CodeMirror-foldgutter",
              "CodeMirror-lint-markers",
              "CodeMirror-linenumbers"
            ],
            foldGutter: true
          } as any
        }
        editorDidMount={editor => {
          performLint(editor);
        }}
        onBeforeChange={(editor, data, value) => {
          this.props.onConfigChange(value);
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
  .react-codemirror2 {
    && {
      width: 100%;
      flex: 1;
    }
  }
  .CodeMirror {
    && {
      height: 100%;
      width: 100%;
    }
  }
  .cm-whitespace {
    /*
      Note: background is a 16x16px PNG containing a semi-transparent gray dot. 8.4px
      is the exact width of a character in Codemirror's monospace font. It's consistent
      in Firefox and Chrome and doesn't change on zoom in / out, but may need to be
      modified if we change the Codemirror font.
    */
    background: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABGdBTUEAALGPC/xhBQAAAFJJREFUOBFjYBgFAx8CjLiccPnyZXFmZmY9kPzfv38v6erqvsSmlgmbIEgMpJmRkZEDhGEGYVOL0wBsirGJ4TQA5Oz/////AGEQG5vmUbHBEgIA9y0YCFtvw70AAAAASUVORK5CYII=') center left / 8.4px 8.4px repeat-x;
  }
  .cm-whitespace.CodeMirror-lint-mark-error {
    background: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABGdBTUEAALGPC/xhBQAAAFJJREFUOBFjYBgFAx8CjLiccPnyZXFmZmY9kPzfv38v6erqvsSmlgmbIEgMpJmRkZEDhGEGYVOL0wBsirGJ4TQA5Oz/////AGEQG5vmUbHBEgIA9y0YCFtvw70AAAAASUVORK5CYII=') center left / 8.4px 8.4px repeat-x, url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAQAAAADCAYAAAC09K7GAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9sJDw4cOCW1/KIAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAAAHElEQVQI12NggIL/DAz/GdA5/xkY/qPKMDAwAADLZwf5rvm+LQAAAABJRU5ErkJggg==") left bottom repeat-x;
  }
`;
