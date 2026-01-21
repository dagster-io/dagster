import CodeMirror from 'codemirror';
import 'codemirror/addon/edit/closebrackets';
import 'codemirror/addon/edit/matchbrackets';
import 'codemirror/addon/fold/brace-fold';
import 'codemirror/addon/fold/foldcode';
import 'codemirror/addon/fold/foldgutter';
import 'codemirror/addon/fold/foldgutter.css';
import 'codemirror/addon/lint/lint';
import 'codemirror/addon/lint/lint.css';
import 'codemirror/mode/javascript/javascript';
import * as React from 'react';

import {DagsterCodeMirrorStyle} from './DagsterCodeMirrorStyle';
import {RawCodeMirror} from './RawCodeMirror';
import {useJsonValidator} from './configeditor/codemirror-json/hooks/useJsonValidator';
import {createJsonExtraKeys} from './configeditor/codemirror-json/utils/codeMirrorJsonUtils';

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
  const validateJson = useJsonValidator();

  const finalOptions = React.useMemo(() => {
    // Merge extraKeys: Default keys + Prop keys
    const defaultExtraKeys = createJsonExtraKeys();
    const propExtraKeys = options?.extraKeys || {};
    const combinedExtraKeys =
      typeof propExtraKeys === 'string' ? propExtraKeys : {...defaultExtraKeys, ...propExtraKeys};

    // Lint options
    const lintOptions = options?.lint ?? {getAnnotations: validateJson, async: false};

    // Theme logic
    const themeArray = Array.isArray(theme) ? theme : theme ? [theme] : [];
    const themeString = [...themeArray, 'dagster'].join(' ');

    return {
      mode: {name: 'javascript', json: true},
      lineNumbers: true,
      lineWrapping: true,
      matchBrackets: true,

      // Disable default auto-close to allow our manual override to work
      autoCloseBrackets: false,

      foldGutter: true,
      gutters: ['CodeMirror-lint-markers', 'CodeMirror-linenumbers', 'CodeMirror-foldgutter'],
      smartIndent: true,
      indentUnit: 2,
      tabSize: 2,
      indentWithTabs: false,
      electricChars: true,
      ...options,
      lint: lintOptions,
      extraKeys: combinedExtraKeys,
      theme: themeString,
    };
  }, [options, validateJson, theme]);

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
