import 'codemirror/addon/comment/comment';
import 'codemirror/addon/dialog/dialog';
import 'codemirror/addon/fold/foldgutter';
import 'codemirror/addon/fold/foldgutter.css';
import 'codemirror/addon/fold/indent-fold';
import 'codemirror/addon/hint/show-hint';
import 'codemirror/addon/hint/show-hint.css';
import 'codemirror/addon/lint/lint.css';
import 'codemirror/addon/search/jump-to-line';
import 'codemirror/addon/search/search';
import 'codemirror/addon/search/searchcursor';
import 'codemirror/keymap/sublime';

import {Editor} from 'codemirror';
import debounce from 'lodash/debounce';
import * as React from 'react';
import {createGlobalStyle} from 'styled-components/macro';
import * as yaml from 'yaml';

import {StyledCodeMirror} from './CodeMirror';
import {patchLint} from './configeditor/codemirror-yaml/lint';
import {
  YamlModeValidateFunction,
  expandAutocompletionContextAtCursor,
  findRangeInDocumentFromPath,
  YamlModeValidationResult,
} from './configeditor/codemirror-yaml/mode'; // eslint-disable-line import/no-duplicates
import {ConfigEditorHelpContext} from './configeditor/types/ConfigEditorHelpContext';
import {ConfigSchema} from './configeditor/types/ConfigSchema';

export {isHelpContextEqual} from './configeditor/isHelpContextEqual';
export {ConfigEditorHelp} from './configeditor/ConfigEditorHelp';

export type {ConfigEditorHelpContext, ConfigSchema, YamlModeValidationResult};

patchLint();

interface ConfigEditorProps {
  configCode: string;
  readOnly: boolean;
  configSchema?: ConfigSchema | null;

  checkConfig: YamlModeValidateFunction;
  onConfigChange: (newValue: string) => void;
  onHelpContextChange: (helpContext: ConfigEditorHelpContext | null) => void;
}

const AUTO_COMPLETE_AFTER_KEY = /^[a-zA-Z0-9_@(]$/;
const performLint = debounce((editor: any) => {
  editor.performLint();
}, 1000);

const ConfigEditorStyle = createGlobalStyle`
  .react-codemirror2 .CodeMirror.cm-s-config-editor {
    height: initial;
    position: absolute;
    inset: 0;
  }
`;

export class ConfigEditor extends React.Component<ConfigEditorProps> {
  _editor?: Editor;

  componentDidUpdate(prevProps: ConfigEditorProps) {
    if (!this._editor) {
      return;
    }
    if (prevProps.configSchema === this.props.configSchema) {
      return;
    }
    this.performInitialPass();
  }

  shouldComponentUpdate(prevProps: ConfigEditorProps) {
    // Unfortunately, updates to the ConfigEditor clear the linter highlighting for
    // unknown reasons and they're recalculated asynchronously. To prevent flickering,
    // only update if our input has meaningfully changed.
    return (
      prevProps.configCode !== this.props.configCode ||
      prevProps.readOnly !== this.props.readOnly ||
      prevProps.configSchema !== this.props.configSchema
    );
  }

  // Public API

  moveCursor = (line: number, ch: number) => {
    if (!this._editor) {
      return;
    }
    this._editor.setCursor(line, ch, {scroll: false});
    const {clientHeight} = this._editor.getScrollInfo();
    const {left, top} = this._editor.cursorCoords(true, 'local');
    const offsetFromTop = 20;

    this._editor?.scrollIntoView({
      left,
      right: left,
      top: top - offsetFromTop,
      bottom: top + (clientHeight - offsetFromTop),
    });
    this._editor.focus();
  };

  moveCursorToPath = (path: string[]) => {
    if (!this._editor) {
      return;
    }
    const codeMirrorDoc = this._editor.getDoc();
    const yamlDoc = yaml.parseDocument(this.props.configCode);
    const range = findRangeInDocumentFromPath(yamlDoc, path, 'key');
    if (!range) {
      return;
    }
    const from = codeMirrorDoc.posFromIndex(range ? range.start : 0) as CodeMirror.Position;
    this.moveCursor(from.line, from.ch);
  };

  // End Public API

  performInitialPass() {
    // update the gutter and redlining
    performLint(this._editor);

    // update the contextual help based on the configSchema and content
    const {context} = expandAutocompletionContextAtCursor(this._editor);
    this.props.onHelpContextChange(context ? {type: context.closestMappingType} : null);
  }

  render() {
    // Unfortunately, CodeMirror is too intense to be simulated in the JSDOM "virtual" DOM.
    // Until we run tests against something like selenium, trying to render the editor in
    // tests have to stop here.
    if (process.env.NODE_ENV === 'test') {
      return <span />;
    }

    return (
      <div style={{flex: 1, position: 'relative'}}>
        <ConfigEditorStyle />
        <StyledCodeMirror
          value={this.props.configCode}
          theme={['config-editor']}
          options={
            {
              mode: 'yaml',
              lineNumbers: true,
              readOnly: this.props.readOnly,
              indentUnit: 2,
              smartIndent: true,
              showCursorWhenSelecting: true,
              lintOnChange: false,
              lint: {
                checkConfig: this.props.checkConfig,
                lintOnChange: false,
                onUpdateLinting: false,
              },
              hintOptions: {
                completeSingle: false,
                closeOnUnfocus: false,
                schema: this.props.configSchema,
              },
              keyMap: 'sublime',
              extraKeys: {
                'Cmd-Space': (editor: any) => editor.showHint({completeSingle: true}),
                'Ctrl-Space': (editor: any) => editor.showHint({completeSingle: true}),
                'Alt-Space': (editor: any) => editor.showHint({completeSingle: true}),
                'Shift-Tab': (editor: any) => editor.execCommand('indentLess'),
                Tab: (editor: any) => editor.execCommand('indentMore'),
                // Persistent search box in Query Editor
                'Cmd-F': 'findPersistent',
                'Ctrl-F': 'findPersistent',
              },
              gutters: [
                'CodeMirror-foldgutter',
                'CodeMirror-lint-markers',
                'CodeMirror-linenumbers',
              ],
              foldGutter: true,
            } as any
          }
          editorDidMount={(editor) => {
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
              const {context} = expandAutocompletionContextAtCursor(editor);
              this.props.onHelpContextChange(context ? {type: context.closestMappingType} : null);
            }
          }}
          onChange={(editor: Editor) => {
            performLint(editor);
          }}
          onBlur={(editor: Editor) => {
            performLint(editor);
          }}
          onKeyUp={(editor, event: KeyboardEvent) => {
            if (AUTO_COMPLETE_AFTER_KEY.test(event.key)) {
              editor.execCommand('autocomplete');
            }
          }}
        />
      </div>
    );
  }
}
