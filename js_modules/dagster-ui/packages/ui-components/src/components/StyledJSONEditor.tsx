import clsx from 'clsx';
import CodeMirror from 'codemirror';
import 'codemirror/addon/edit/matchbrackets';
import 'codemirror/mode/javascript/javascript';
import * as React from 'react';
import styled from 'styled-components';

import {DagsterCodeMirrorStyle} from './DagsterCodeMirrorStyle';
import {RawCodeMirror} from './RawCodeMirror';
import * as Colors from '../palettes/Color';
import {createSmartBracketKeyMap} from './configeditor/codemirror-json/codeMirrorJson';

const EditorContainer = styled.div`
  border: 1px solid ${Colors.keylineDefault()};
  border-radius: 4px;
  overflow: hidden;

  .CodeMirror {
    &:focus-visible {
      outline: none;
    }

    &:focus {
      outline: none;
    }

    .cm-property {
      color: ${Colors.textBlue()};
    }
  }
`;

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

  const finalOptions = React.useMemo(() => {
    return {
      mode: {name: 'javascript', json: true},
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
        ...createSmartBracketKeyMap(),
        ...(typeof options?.extraKeys === 'object' ? options.extraKeys : {}),
      },
    } as CodeMirror.EditorConfiguration;
  }, [options, theme]);
  return (
    <EditorContainer className={className} style={style}>
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
    </EditorContainer>
  );
};
