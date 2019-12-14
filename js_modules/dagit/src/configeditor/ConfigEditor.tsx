import * as React from "react";
import { createGlobalStyle } from "styled-components/macro";
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
import { Editor } from "codemirror";
import {
  ConfigEditorEnvironmentSchemaFragment,
  ConfigEditorEnvironmentSchemaFragment_allConfigTypes
} from "./types/ConfigEditorEnvironmentSchemaFragment";
import "./codemirror-yaml/mode";
import {
  LintJson as YamlModeLintJson,
  expandAutocompletionContextAtCursor
} from "./codemirror-yaml/mode";
import { debounce } from "../Util";

export function isHelpContextEqual(
  prev: ConfigEditorHelpContext | null,
  next: ConfigEditorHelpContext | null
) {
  return (prev && prev.type.key) === (next && next.type.key);
}

interface ConfigEditorProps {
  checkConfig: YamlModeLintJson;
  configCode: string;
  onConfigChange: (newValue: string) => void;
  onHelpContextChange: (helpContext: ConfigEditorHelpContext | null) => void;
  environmentSchema?: ConfigEditorEnvironmentSchemaFragment;
  readOnly: boolean;
  showWhitespace: boolean;
}

const AUTO_COMPLETE_AFTER_KEY = /^[a-zA-Z0-9_@(]$/;
const performLint = debounce((editor: any) => {
  editor.performLint();
}, 1000);

const CodeMirrorShimStyle = createGlobalStyle`
  .react-codemirror2 {
    height: 100%;
    flex: 1;
    position: relative;
  }
  .react-codemirror2 .CodeMirror {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    height: initial;
  }
`;
const CodeMirrorWhitespaceStyle = createGlobalStyle`
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

export interface ConfigEditorHelpContext {
  type: ConfigEditorEnvironmentSchemaFragment_allConfigTypes;
}

export class ConfigEditor extends React.Component<ConfigEditorProps> {
  _editor?: Editor;

  componentDidUpdate(prevProps: ConfigEditorProps) {
    if (!this._editor) return;
    if (prevProps.environmentSchema === this.props.environmentSchema) return;
    this.performInitialPass();
  }

  performInitialPass() {
    // update the gutter and redlining
    performLint(this._editor);

    // update the contextual help based on the environmentSchema and content
    const { context } = expandAutocompletionContextAtCursor(this._editor);
    this.props.onHelpContextChange(
      context ? { type: context.closestCompositeType } : null
    );
  }

  render() {
    // Unfortunately, CodeMirror is too intense to be simulated in the JSDOM "virtual" DOM.
    // Until we run tests against something like selenium, trying to render the editor in
    // tests have to stop here.
    if (process.env.NODE_ENV === "test") {
      return <span />;
    }

    return (
      <div style={{ flex: 1, position: "relative" }}>
        <CodeMirrorShimStyle />
        {this.props.showWhitespace ? <CodeMirrorWhitespaceStyle /> : null}
        <CodeMirrorReact
          value={this.props.configCode}
          options={
            {
              mode: "yaml",
              theme: "material",
              lineNumbers: true,
              readOnly: this.props.readOnly,
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
                schema: this.props.environmentSchema
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
                "Ctrl-F": "findPersistent",
                "Cmd-Z": (editor: any) => editor.undo(),
                "Cmd-Y": (editor: any) => editor.redo()
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
            this._editor = editor;
            this.performInitialPass();
          }}
          onBeforeChange={(editor, data, value) => {
            this.props.onConfigChange(value);
          }}
          onCursorActivity={(editor: any) => {
            if (editor.getSelection().length) {
              this.props.onHelpContextChange(null);
            } else {
              const { context } = expandAutocompletionContextAtCursor(editor);
              this.props.onHelpContextChange(
                context ? { type: context.closestCompositeType } : null
              );
            }
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
      </div>
    );
  }
}
