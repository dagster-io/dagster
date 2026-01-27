import CodeMirror from 'codemirror';
import 'codemirror/addon/edit/closebrackets';
import 'codemirror/addon/edit/matchbrackets';
import 'codemirror/addon/fold/brace-fold';
import 'codemirror/addon/fold/foldcode';
import 'codemirror/addon/fold/foldgutter';
import 'codemirror/addon/fold/foldgutter.css';
import 'codemirror/addon/hint/show-hint';
import 'codemirror/addon/hint/show-hint.css';
import 'codemirror/mode/javascript/javascript';
import 'codemirror/addon/lint/lint';
import 'codemirror/addon/lint/lint.css';
import * as React from 'react';

import {DagsterCodeMirrorStyle} from './DagsterCodeMirrorStyle';
import {RawCodeMirror} from './RawCodeMirror';
import {
  JsonHintToken,
  registerJsonHint,
} from './configeditor/codemirror-json/utils/codeMirrorJsonHint';
import {
  createSmartBracketKeyMap,
  registerJsonLint,
} from './configeditor/codemirror-json/utils/codeMirrorJsonUtils';

// Register JSON linter and hint helper
registerJsonLint();
registerJsonHint();

export interface StyledJSONEditorProps {
  value: string;
  onChange?: (value: string) => void;
  onReady?: (instance: CodeMirror.Editor) => void;
  options?: CodeMirror.EditorConfiguration;
  theme?: string[] | string;
  className?: string;
  style?: React.CSSProperties;
  /** Tokens for autocomplete hints (shown when typing { inside strings) */
  additionalAutocompleteTokens?: JsonHintToken[];
}

export const StyledJSONEditor = (props: StyledJSONEditorProps) => {
  const {
    options,
    theme,
    value,
    onChange,
    onReady,
    className,
    style,
    additionalAutocompleteTokens,
    ...rest
  } = props;

  const finalOptions = React.useMemo(() => {
    const themeArray = Array.isArray(theme) ? theme : theme ? [theme] : [];
    const themeString = [...themeArray, 'dagster'].join(' ');

    return {
      mode: {name: 'javascript', json: true},

      // Disable native auto-close - using smart context-aware handlers instead
      autoCloseBrackets: false,

      matchBrackets: true,
      lineNumbers: true,
      lineWrapping: true,
      foldGutter: true,
      gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter', 'CodeMirror-lint-markers'],
      lint: true,
      smartIndent: true,
      indentUnit: 2,
      tabSize: 2,
      indentWithTabs: false,
      electricChars: true,
      ...options,
      theme: themeString,
      extraKeys: {
        // Smart auto-close brackets: only outside strings
        ...createSmartBracketKeyMap(),
        // Ctrl-Space to trigger autocomplete
        'Ctrl-Space': (cm: CodeMirror.Editor) => {
          cm.showHint({completeSingle: false});
        },
        ...(typeof options?.extraKeys === 'object' ? options.extraKeys : {}),
      },
      // Pass tokens for hint helper (extends standard ShowHintOptions)
      hintOptions: {
        tokens: additionalAutocompleteTokens || [],
      },
    } as CodeMirror.EditorConfiguration;
  }, [options, theme, additionalAutocompleteTokens]);

  const handlers = React.useMemo(
    () => ({
      onChange: (instance: CodeMirror.Editor) => onChange?.(instance.getValue()),
      onReady: (instance: CodeMirror.Editor) => onReady?.(instance),
    }),
    [onChange, onReady],
  );

  return (
    <div className={className} style={style}>
      <DagsterCodeMirrorStyle />
      <RawCodeMirror value={value} {...rest} handlers={handlers} options={finalOptions} />
    </div>
  );
};
