import 'codemirror/addon/comment/comment';
import 'codemirror/addon/dialog/dialog';
import 'codemirror/addon/fold/foldgutter';
import 'codemirror/addon/fold/foldgutter.css';
import 'codemirror/addon/fold/indent-fold';
import 'codemirror/addon/fold/brace-fold';
import 'codemirror/addon/hint/show-hint';
import 'codemirror/addon/hint/show-hint.css';
import 'codemirror/addon/lint/lint.css';
import 'codemirror/addon/search/jump-to-line';
import 'codemirror/addon/search/search';
import 'codemirror/addon/search/searchcursor';
import 'codemirror/addon/edit/closebrackets';
import 'codemirror/addon/edit/matchbrackets';
import 'codemirror/addon/lint/lint';
import 'codemirror/addon/lint/json-lint';
import 'codemirror/mode/javascript/javascript';
import 'codemirror/keymap/sublime';

import CodeMirror from 'codemirror';
import debounce from 'lodash/debounce';
import {forwardRef, useCallback, useImperativeHandle, useMemo, useRef, useState} from 'react';
import {createGlobalStyle} from 'styled-components';
import * as yaml from 'yaml';

import {Box} from './Box';
import {ButtonGroup, ButtonGroupItem} from './ButtonGroup';
import {Colors} from './Color';
import {StyledRawCodeMirror} from './StyledRawCodeMirror';
import {patchLint} from './configeditor/codemirror-yaml/lint';
import {
  YamlModeValidateFunction,
  YamlModeValidationResult,
  expandAutocompletionContextAtCursor,
  findRangeInDocumentFromPath,
} from './configeditor/codemirror-yaml/mode';
import {ConfigEditorHelpContext} from './configeditor/types/ConfigEditorHelpContext';
import {ConfigSchema} from './configeditor/types/ConfigSchema';
import {FontFamily} from './styles';

export {isHelpContextEqual} from './configeditor/isHelpContextEqual';
export {ConfigEditorHelp} from './configeditor/ConfigEditorHelp';

export type {ConfigEditorHelpContext, ConfigSchema, YamlModeValidationResult};

/** Content type for the editor */
export type ConfigEditorContentType = 'yaml' | 'json';

/** Mode for Edit/Preview toggle */
export type ConfigEditorMode = 'edit' | 'preview';

/** Transform function for preview mode */
export type ContentTransformer = (content: string) => string;

patchLint();

interface ConfigEditorProps {
  configCode: string;
  readOnly: boolean;
  configSchema?: ConfigSchema | null;

  // YAML mode props (optional when using JSON mode)
  checkConfig?: YamlModeValidateFunction;
  onConfigChange: (newValue: string) => void;
  onHelpContextChange?: (helpContext: ConfigEditorHelpContext | null) => void;

  // Content type support
  contentType?: ConfigEditorContentType;

  // Edit/Preview mode
  showModeToggle?: boolean;
  previewTransform?: ContentTransformer;
  initialMode?: ConfigEditorMode;

  // JSON-specific features
  enhancedJson?: boolean;

  // UI customization
  header?: React.ReactNode;
  minHeight?: number;
  maxHeight?: number;
  lineNumbers?: boolean;
}

const AUTO_COMPLETE_AFTER_KEY = /^[a-zA-Z0-9_@(]$/;
const performLint = debounce((editor: any) => {
  editor.performPatchedLint();
}, 1000);

const performInitialPass = (
  editor: CodeMirror.Editor,
  onHelpContextChange?: (helpContext: ConfigEditorHelpContext | null) => void,
) => {
  // update the gutter and redlining
  performLint(editor);

  // update the contextual help based on the configSchema and content
  if (onHelpContextChange) {
    const {context} = expandAutocompletionContextAtCursor(editor);
    onHelpContextChange(context ? {type: context.closestMappingType} : null);
  }
};

// Static mode buttons - defined outside component to avoid re-creation on each render
const MODE_BUTTONS: ButtonGroupItem<string>[] = [
  {id: 'edit', icon: 'edit', label: 'Edit'},
  {id: 'preview', icon: 'visibility', label: 'Preview'},
];

interface LintError {
  from: CodeMirror.Position;
  to: CodeMirror.Position;
  message: string;
  severity: 'error' | 'warning';
}

/**
 * Custom JSON linter for CodeMirror that parses JSON and returns lint errors.
 */
const jsonLint = (text: string): LintError[] => {
  const errors: LintError[] = [];

  // Skip linting for empty or whitespace-only content
  if (!text.trim()) return errors;

  try {
    JSON.parse(text);
  } catch (e) {
    const error = e as Error;

    let line = 0;
    let col = 0;

    // Try to find "position X" in error message
    const posMatch = error.message.match(/position (\d+)/);
    if (posMatch && posMatch[1]) {
      const pos = parseInt(posMatch[1], 10);
      const lines = text.substring(0, pos).split('\n');
      line = lines.length - 1;
      col = lines[lines.length - 1]?.length ?? 0;
    } else {
      // Fallback: try to parse "line X" from error message
      const lineMatch = error.message.match(/line (\d+)/i);
      if (lineMatch && lineMatch[1]) {
        line = parseInt(lineMatch[1], 10) - 1;
      }
    }

    errors.push({
      from: CodeMirror.Pos(line, col),
      to: CodeMirror.Pos(line, col + 1),
      message: error.message,
      severity: 'error',
    });
  }
  return errors;
};

const ConfigEditorStyle = createGlobalStyle`
  .CodeMirror.cm-s-config-editor {
    background-color: ${Colors.backgroundLight()};
    height: initial;
    position: absolute;
    inset: 0;
  }

  .dagster.CodeMirror-hints {
    background-color: ${Colors.backgroundDefault()};
    box-shadow: 2px 3px 5px ${Colors.shadowDefault()};
    border: none;
    font-family: ${FontFamily.monospace};
    font-size: 14px;
    z-index: 100;
    border-radius: 8px;
    overflow: hidden;
    padding: 2px;
    margin-top: 2px;
  }

  .dagster .CodeMirror-hint {
    border-radius: 6px;
    padding: 4px 8px;
    color: ${Colors.textDefault()};
  }

  .dagster .CodeMirror-hint-active {
    background-color: ${Colors.backgroundBlue()};
    color: ${Colors.textDefault()};
  }
`;

export type ConfigEditorHandle = {
  moveCursor: (line: number, ch: number) => void;
  moveCursorToPath: (path: string[]) => void;
};

export const NewConfigEditor = forwardRef<ConfigEditorHandle, ConfigEditorProps>((props, ref) => {
  const {
    configCode,
    checkConfig,
    readOnly,
    configSchema,
    onConfigChange,
    onHelpContextChange,
    contentType = 'yaml',
    showModeToggle = false,
    previewTransform,
    initialMode = 'edit',
    enhancedJson = true,
    header,
    minHeight,
    maxHeight,
    lineNumbers = true,
  } = props;

  const editor = useRef<CodeMirror.Editor | null>(null);
  const [mode, setMode] = useState<ConfigEditorMode>(initialMode);

  const handleModeChange = useCallback((id: string) => {
    setMode(id as ConfigEditorMode);
  }, []);

  const activeItems = useMemo(() => new Set([mode]), [mode]);

  const previewValue = useMemo(() => {
    if (previewTransform) {
      return previewTransform(configCode);
    }
    return configCode;
  }, [configCode, previewTransform]);

  const isPreviewMode = mode === 'preview';
  const displayValue = isPreviewMode ? previewValue : configCode;
  const isEditorReadOnly = readOnly || isPreviewMode;

  useImperativeHandle(ref, () => {
    const moveCursor = (line: number, ch: number) => {
      if (!editor.current) {
        return;
      }

      editor.current.setCursor(line, ch, {scroll: false});
      const {clientHeight} = editor.current.getScrollInfo();
      const {left, top} = editor.current.cursorCoords(true, 'local');
      const offsetFromTop = 20;

      editor.current?.scrollIntoView({
        left,
        right: left,
        top: top - offsetFromTop,
        bottom: top + (clientHeight - offsetFromTop),
      });
      editor.current.focus();
    };

    const moveCursorToPath = (path: string[]) => {
      if (!editor.current) {
        return;
      }
      const codeMirrorDoc = editor.current.getDoc();
      const yamlDoc = yaml.parseDocument(configCode);
      const range = findRangeInDocumentFromPath(yamlDoc, path, 'key');
      if (!range) {
        return;
      }
      const from = codeMirrorDoc.posFromIndex(range ? range.start : 0) as CodeMirror.Position;
      moveCursor(from.line, from.ch);
    };

    return {moveCursor, moveCursorToPath};
  }, [configCode]);

  const options = useMemo(() => {
    // JSON mode options
    if (contentType === 'json') {
      const baseExtraKeys: CodeMirror.KeyMap = {
        'Shift-Tab': (ed: any) => ed.execCommand('indentLess'),
        Tab: (ed: any) => ed.execCommand('indentMore'),
        'Cmd-F': 'findPersistent',
        'Ctrl-F': 'findPersistent',
      };

      const baseOptions: CodeMirror.EditorConfiguration = {
        mode: {name: 'javascript', json: true},
        lineNumbers,
        lineWrapping: false,
        readOnly: isEditorReadOnly,
        tabSize: 2,
        indentWithTabs: false,
        indentUnit: 2,
        keyMap: 'sublime',
        extraKeys: baseExtraKeys,
      };

      if (enhancedJson) {
        return {
          ...baseOptions,
          autoCloseBrackets: true,
          matchBrackets: true,
          foldGutter: true,
          gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter', 'CodeMirror-lint-markers'],
          lint: {
            getAnnotations: jsonLint,
            async: false,
          },
          extraKeys: {
            ...baseExtraKeys,
            'Ctrl-Space': 'autocomplete',
            'Cmd-Space': 'autocomplete',
          },
        };
      }

      return baseOptions;
    }

    // YAML mode options (default)
    return {
      mode: 'yaml',
      lineNumbers,
      readOnly: isEditorReadOnly,
      indentUnit: 2,
      smartIndent: true,
      showCursorWhenSelecting: true,
      lintOnChange: false,
      patchedLint: checkConfig
        ? {
            checkConfig,
            lintOnChange: false,
            onUpdateLinting: false,
          }
        : undefined,
      hintOptions: {
        completeSingle: false,
        schema: configSchema,
      },
      keyMap: 'sublime',
      extraKeys: {
        'Cmd-Space': (editor: any) => editor.showHint({completeSingle: true}),
        'Ctrl-Space': (editor: any) => editor.showHint({completeSingle: true}),
        'Alt-Space': (editor: any) => editor.showHint({completeSingle: true}),
        'Shift-Tab': (editor: any) => editor.execCommand('indentLess'),
        Tab: (editor: any) => editor.execCommand('indentMore'),
        'Cmd-F': 'findPersistent',
        'Ctrl-F': 'findPersistent',
      },
      gutters: ['CodeMirror-foldgutter', 'CodeMirror-lint-markers', 'CodeMirror-linenumbers'],
      foldGutter: true,
    };
  }, [checkConfig, configSchema, isEditorReadOnly, contentType, enhancedJson, lineNumbers]);

  const handlers = useMemo(() => {
    // In preview mode, don't attach change handlers
    if (isPreviewMode) {
      return {
        onReady: (editorInstance: CodeMirror.Editor) => {
          editor.current = editorInstance;
        },
      };
    }

    return {
      onReady: (editorInstance: CodeMirror.Editor) => {
        editor.current = editorInstance;
        if (contentType === 'yaml') {
          performInitialPass(editorInstance, onHelpContextChange);
        }
      },
      onChange: (editorInstance: CodeMirror.Editor) => {
        onConfigChange(editorInstance.getValue());
        if (contentType === 'yaml') {
          performLint(editorInstance);
        }
      },
      onCursorActivity:
        contentType === 'yaml' && onHelpContextChange
          ? (editorInstance: CodeMirror.Editor) => {
              if (editorInstance.getSelection().length) {
                onHelpContextChange(null);
              } else {
                const {context} = expandAutocompletionContextAtCursor(editorInstance);
                onHelpContextChange(context ? {type: context.closestMappingType} : null);
              }
            }
          : undefined,
      onBlur:
        contentType === 'yaml'
          ? (editorInstance: CodeMirror.Editor) => {
              performLint(editorInstance);
            }
          : undefined,
      onKeyUp: (editorInstance: CodeMirror.Editor, event: Event) => {
        if (event instanceof KeyboardEvent && AUTO_COMPLETE_AFTER_KEY.test(event.key)) {
          editorInstance.execCommand('autocomplete');
        }
      },
    };
  }, [onConfigChange, onHelpContextChange, contentType, isPreviewMode]);

  // Unfortunately, CodeMirror is too intense to be simulated in the JSDOM "virtual" DOM.
  // Until we run tests against something like selenium, trying to render the editor in
  // tests have to stop here.
  if (process.env.NODE_ENV === 'test') {
    return <span />;
  }

  const containerStyle: React.CSSProperties = {
    flex: 1,
    position: 'relative',
    ...(minHeight && {minHeight}),
    ...(maxHeight && {maxHeight}),
    ...(showModeToggle && {
      border: '1px solid var(--color-border-default)',
      borderRadius: 4,
      overflow: 'hidden',
    }),
  };

  const editorContent = (
    <div style={containerStyle}>
      <ConfigEditorStyle />
      <StyledRawCodeMirror
        key={mode}
        value={displayValue}
        theme={['config-editor']}
        options={options}
        handlers={handlers}
      />
    </div>
  );

  // If no header and no mode toggle, return simple layout
  if (!header && !showModeToggle) {
    return editorContent;
  }

  // With header or mode toggle, wrap in Box layout
  return (
    <Box flex={{direction: 'column', gap: 8}}>
      {(header || showModeToggle) && (
        <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
          {header ?? <div />}
          {showModeToggle && (
            <ButtonGroup
              activeItems={activeItems}
              buttons={MODE_BUTTONS}
              onClick={handleModeChange}
            />
          )}
        </Box>
      )}
      {editorContent}
    </Box>
  );
});

NewConfigEditor.displayName = 'NewConfigEditor';
