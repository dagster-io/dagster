import {Colors, Icon, TextInputStyles} from '@dagster-io/ui-components';
import CodeMirror, {Editor} from 'codemirror';
import {useLayoutEffect, useMemo, useRef} from 'react';
import styled, {createGlobalStyle} from 'styled-components';

import {createAssetSelectionHint} from './AssetSelectionAutoComplete';
import {lintAssetSelection} from './AssetSelectionLinter';
import {assetSelectionMode} from './AssetSelectionMode';
import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {useUpdatingRef} from '../../hooks/useUpdatingRef';
import {placeholderTextForItems} from '../../ui/GraphQueryInput';

import 'codemirror/addon/edit/closebrackets';
import 'codemirror/lib/codemirror.css';
import 'codemirror/addon/hint/show-hint';
import 'codemirror/addon/hint/show-hint.css';
import 'codemirror/addon/lint/lint';
import 'codemirror/addon/lint/lint.css';
import 'codemirror/addon/display/placeholder';

interface AssetSelectionInputProps {
  assets: AssetGraphQueryItem[];
  value: string;
  onChange: (value: string) => void;
}

export const AssetSelectionInput = ({value, onChange, assets}: AssetSelectionInputProps) => {
  const editorRef = useRef<HTMLDivElement>(null);
  const cmInstance = useRef<CodeMirror.Editor | null>(null);

  const currentValueRef = useRef(value);

  const hintRef = useUpdatingRef(useMemo(() => createAssetSelectionHint(assets), [assets]));

  useLayoutEffect(() => {
    if (editorRef.current && !cmInstance.current) {
      // Define the custom mode
      CodeMirror.defineMode('assetSelection', assetSelectionMode);

      // Initialize CodeMirror
      cmInstance.current = CodeMirror(editorRef.current, {
        value,
        mode: 'assetSelection',
        lineNumbers: false,
        lineWrapping: false,
        scrollbarStyle: 'native',
        autoCloseBrackets: true,
        lint: {
          getAnnotations: lintAssetSelection,
          async: false,
        },
        placeholder: placeholderTextForItems('Type an asset subset…', assets),
        extraKeys: {
          'Ctrl-Space': 'autocomplete',
          Tab: (cm: Editor) => {
            cm.replaceSelection('  ', 'end');
          },
        },
      });

      cmInstance.current.setSize('100%', 20);

      // Enforce single line by preventing newlines
      cmInstance.current.on('beforeChange', (_instance: Editor, change) => {
        if (change.text.some((line) => line.includes('\n'))) {
          change.cancel();
        }
      });

      // Update parent component on changes
      cmInstance.current.on('change', (instance: Editor, change) => {
        const newValue = instance.getValue();
        currentValueRef.current = newValue;
        onChange(newValue);

        if (change.origin === 'complete' && change.text[0]?.endsWith(')')) {
          // Set cursor inside the right parenthesis
          const cursor = instance.getCursor();
          instance.setCursor({...cursor, ch: cursor.ch - 1});
        }
      });

      // Autocomplete on input
      cmInstance.current.on('inputRead', (instance: Editor) => {
        console.log('show hint');
        instance.showHint({hint: hintRef.current, completeSingle: false});
      });

      cmInstance.current.on('cursorActivity', (instance: Editor) => {
        console.log('show hint');
        instance.showHint({hint: hintRef.current, completeSingle: false});
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update CodeMirror when value prop changes
  useLayoutEffect(() => {
    const noNewLineValue = value.replace('\n', ' ');
    if (cmInstance.current && cmInstance.current.getValue() !== noNewLineValue) {
      const instance = cmInstance.current;
      const cursor = instance.getCursor();
      instance.setValue(noNewLineValue);
      instance.setCursor(cursor);
      requestAnimationFrame(() => {
        instance.showHint({hint: hintRef.current, completeSingle: false});
      });
    }
  }, [hintRef, value]);

  return (
    <>
      <GlobalHintStyles />
      <InputDiv
        style={{display: 'grid', gridTemplateColumns: 'auto 1fr auto', alignItems: 'center'}}
      >
        <Icon name="op_selector" />
        <div ref={editorRef} />
        <Icon name="info" />
      </InputDiv>
    </>
  );
};

const InputDiv = styled.div`
  height: 32px;
  width: 100%;
  ${TextInputStyles}
  flex-shrink: 1;

  .CodeMirror-placeholder.CodeMirror-placeholder.CodeMirror-placeholder {
    color: ${Colors.textLighter()};
  }

  .CodeMirror-vscrollbar,
  .CodeMirror-hscrollbar {
    display: none !important;
  }

  .CodeMirror-sizer,
  .CodeMirror-lines {
    height: 20px !important;
    padding: 0;
  }

  .CodeMirror-cursor.CodeMirror-cursor {
    border-color: ${Colors.textLight()};
  }

  .CodeMirror {
    background: transparent;
    color: ${Colors.textDefault()};
  }

  .cm-attribute {
    color: ${Colors.textCyan()};
    font-weight: bold;
  }

  .cm-operator {
    color: ${Colors.textRed()};
    font-weight: bold;
  }

  .cm-string {
    color: ${Colors.textGreen()};
  }

  .cm-function {
    color: ${Colors.textYellow()};
    font-style: italic;
  }

  .cm-punctuation {
    color: ${Colors.textDefault()};
  }

  .cm-error {
    text-decoration-line: underline;
    text-decoration-style: wavy;
    text-decoration-color: ${Colors.accentRed()};
  }
`;

const GlobalHintStyles = createGlobalStyle`
  .CodeMirror-hints {
    background: ${Colors.popoverBackground()};
    border: none;
    border-radius: 4px;
    padding: 8px 4px;
    .CodeMirror-hint {
      border-radius: 4px;
      font-size: 14px;
      padding: 6px 8px 6px 12px;
      color: ${Colors.textDefault()};
      &.CodeMirror-hint-active {
        background-color: ${Colors.backgroundBlue()};
        color: ${Colors.textDefault()};
      }
    }
  }
`;
