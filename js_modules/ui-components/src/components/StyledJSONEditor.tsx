import clsx from 'clsx';
import CodeMirror from 'codemirror';
import 'codemirror/addon/edit/matchbrackets';
import 'codemirror/mode/javascript/javascript';
import 'codemirror/mode/jinja2/jinja2';
import * as React from 'react';

import {DagsterCodeMirrorStyle} from './DagsterCodeMirrorStyle';
import {RawCodeMirror} from './RawCodeMirror';
import {createSmartBracketKeyMap} from './configeditor/codemirror-json/codeMirrorJson';
import styles from './css/StyledJSONEditor.module.css';

const JINJA_RE = /\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\}/s;
const JSON_MODE = {name: 'javascript', json: true};

const detectMode = (value: string): CodeMirror.EditorConfiguration['mode'] => {
  const trimmed = value.trimStart();
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    if (!JINJA_RE.test(value)) {
      return JSON_MODE;
    }
  }
  if (JINJA_RE.test(value)) {
    return 'jinja2';
  }
  return 'text/plain';
};

export interface StyledJSONEditorProps {
  value: string;
  onChange?: (value: string) => void;
  onReady?: (instance: CodeMirror.Editor) => void;
  options?: CodeMirror.EditorConfiguration;
  theme?: string[] | string;
  className?: string;
  style?: React.CSSProperties;
}

export const StyledJSONEditor = (props: StyledJSONEditorProps) => {
  const {options, theme, value, onChange, onReady, className, style, ...rest} = props;

  const resolvedMode = React.useRef(detectMode(value)).current;

  const finalOptions = React.useMemo(() => {
    return {
      mode: resolvedMode,
      matchBrackets: true,
      lineNumbers: true,
      lineWrapping: true,
      gutters: ['CodeMirror-linenumbers'],
      smartIndent: true,
      indentUnit: 2,
      tabSize: 2,
      ...options,
      theme: clsx(theme, 'dagster'),
      extraKeys: {
        ...(typeof resolvedMode !== 'string' ? createSmartBracketKeyMap() : {}),
        ...(typeof options?.extraKeys === 'object' ? options.extraKeys : {}),
      },
    } as CodeMirror.EditorConfiguration;
  }, [options, theme, resolvedMode]);

  return (
    <div className={clsx(styles.editorContainer, className)} style={style}>
      <DagsterCodeMirrorStyle />
      <RawCodeMirror
        value={value}
        {...rest}
        handlers={{
          onChange: (instance) => onChange?.(instance.getValue()),
          onReady: (instance) => onReady?.(instance),
        }}
        options={finalOptions}
      />
    </div>
  );
};
