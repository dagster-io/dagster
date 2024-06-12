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

import debounce from 'lodash/debounce';
import {forwardRef, useImperativeHandle, useMemo, useRef} from 'react';
import {createGlobalStyle} from 'styled-components';
import {v4 as uuidv4} from 'uuid';
import * as yaml from 'yaml';

import {Colors} from './Color';
import {StyledRawCodeMirror} from './StyledRawCodeMirror';
import {patchLint} from './configeditor/codemirror-yaml/lint';
import {
  YamlModeValidationResult,
  expandAutocompletionContextAtCursor,
  findRangeInDocumentFromPath,
} from './configeditor/codemirror-yaml/mode';
import {ConfigEditorHelpContext} from './configeditor/types/ConfigEditorHelpContext';
import {
  ConfigSchema,
  ConfigSchema_allConfigTypes,
  ConfigSchema_allConfigTypes_CompositeConfigType_fields,
} from './configeditor/types/ConfigSchema';

export {isHelpContextEqual} from './configeditor/isHelpContextEqual';
export {ConfigEditorHelp} from './configeditor/ConfigEditorHelp';

export type {ConfigEditorHelpContext, ConfigSchema, YamlModeValidationResult};

patchLint();

interface ConfigEditorProps {
  configCode: string;
  readOnly: boolean;
  jsonSchema: JsonSchema;

  // checkConfig: YamlModeValidateFunction;
  //onConfigChange: (newValue: string) => void;
  //onHelpContextChange: (helpContext: ConfigEditorHelpContext | null) => void;
}

const AUTO_COMPLETE_AFTER_KEY = /^[a-zA-Z0-9_@(]$/;
const performLint = debounce((editor: any) => {
  editor.performLint();
}, 1000);

const performInitialPass = (
  editor: CodeMirror.Editor,
  onHelpContextChange: (helpContext: ConfigEditorHelpContext | null) => void,
) => {
  // update the gutter and redlining
  performLint(editor);

  // update the contextual help based on the configSchema and content
  const {context} = expandAutocompletionContextAtCursor(editor);
  onHelpContextChange(context ? {type: context.closestMappingType} : null);
};

const ConfigEditorStyle = createGlobalStyle`
  .CodeMirror.cm-s-config-editor {
    background-color: ${Colors.backgroundLight()};
    height: initial;
    position: absolute;
    inset: 0;
  }
`;

export type BlueprintConfigEditorHandle = {
  moveCursor: (line: number, ch: number) => void;
  moveCursorToPath: (path: string[]) => void;
};

type JsonSchema = {
  type: string;
  properties: {
    [key: string]: JsonSchema;
  };
  description?: string;
};

const jsonSchemaToConfigSchemaInner = (
  jsonSchema: JsonSchema,
): {
  types: ConfigSchema_allConfigTypes[];
  rootKey: string;
} => {
  console.log(jsonSchema);
  if (jsonSchema.type === 'object') {
    const fieldTypesByKey = Object.entries(jsonSchema.properties).reduce(
      (accum, [key, value]) => {
        accum[key] = jsonSchemaToConfigSchemaInner(value);
        return accum;
      },
      {} as Record<string, {types: ConfigSchema_allConfigTypes[]; rootKey: string}>,
    );

    const fieldEntries = Object.entries(jsonSchema.properties).map(([key, value]) => {
      return {
        __typename: 'ConfigTypeField',
        name: key,
        description: value.description,
        isRequired: false,
        configTypeKey: fieldTypesByKey[key]?.rootKey,
        defaultValueAsJson: null,
      };
    }) as ConfigSchema_allConfigTypes_CompositeConfigType_fields[];

    // root key (generate a random uuid)
    const rootKeyUuid = uuidv4();

    return {
      types: [
        {
          __typename: 'CompositeConfigType',
          key: rootKeyUuid,
          description: jsonSchema.description || null,
          isSelector: false,
          typeParamKeys: [],
          fields: fieldEntries,
        },
        ...Object.values(fieldTypesByKey).flatMap((x) => x.types),
      ],
      rootKey: rootKeyUuid,
    };
  } else {
    const rootKeyUuid = uuidv4();

    return {
      types: [
        {
          __typename: 'RegularConfigType',
          givenName: 'Any',
          key: rootKeyUuid,
          description: '',
          isSelector: false,
          typeParamKeys: [],
        },
      ],
      rootKey: rootKeyUuid,
    };
  }
};

const jsonSchemaToConfigSchema = (jsonSchema: any): ConfigSchema => {
  // get first object in jsonSchema.definitions
  const firstKey = Object.keys(jsonSchema.definitions)[0];
  const firstValue = jsonSchema.definitions[firstKey];
  const {types, rootKey} = jsonSchemaToConfigSchemaInner(firstValue);

  console.log({
    __typename: 'ConfigSchema',
    rootConfigType: {
      __typename: 'CompositeConfigType',
      key: rootKey,
    },
    allConfigTypes: types,
  });
  return {
    __typename: 'ConfigSchema',
    rootConfigType: {
      __typename: 'CompositeConfigType',
      key: rootKey,
    },
    allConfigTypes: types,
  };
};

export const BlueprintConfigEditor = forwardRef<BlueprintConfigEditorHandle, ConfigEditorProps>(
  (props, ref) => {
    const {configCode, readOnly, jsonSchema} = props;
    const editor = useRef<CodeMirror.Editor | null>(null);

    useImperativeHandle(
      ref,
      () => {
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
      },
      [configCode],
    );

    const schema: ConfigSchema = {
      __typename: 'ConfigSchema',
      rootConfigType: {
        __typename: 'CompositeConfigType',
        key: 'root',
      },
      allConfigTypes: [
        {
          __typename: 'CompositeConfigType',
          key: 'root',
          description: null,
          isSelector: false,
          typeParamKeys: [],
          fields: [
            {
              __typename: 'ConfigTypeField',
              name: 'solids',
              description: null,
              isRequired: false,
              configTypeKey: 'solids',
              defaultValueAsJson: null,
            },
          ],
        },
      ],
    };

    const options = useMemo(() => {
      return {
        mode: 'yaml',
        lineNumbers: true,
        readOnly,
        indentUnit: 2,
        smartIndent: true,
        showCursorWhenSelecting: true,
        lintOnChange: false,
        lint: {
          checkConfig: async (_j: any) => {
            return {isValid: true};
          },
          lintOnChange: false,
          onUpdateLinting: false,
        },
        hintOptions: {
          completeSingle: false,
          schema: jsonSchemaToConfigSchema(jsonSchema),
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
        gutters: ['CodeMirror-foldgutter', 'CodeMirror-lint-markers', 'CodeMirror-linenumbers'],
        foldGutter: true,
      };
    }, [jsonSchema, readOnly]);

    const handlers = useMemo(() => {
      return {
        onReady: (editorInstance: CodeMirror.Editor) => {
          editor.current = editorInstance;
          //   performInitialPass(editorInstance, onHelpContextChange);
        },
        onChange: (editorInstance: CodeMirror.Editor) => {
          // onConfigChange(editorInstance.getValue());
          performLint(editorInstance);
        },
        onCursorActivity: (editorInstance: CodeMirror.Editor) => {
          if (editorInstance.getSelection().length) {
            //   onHelpContextChange(null);
          } else {
            const {context} = expandAutocompletionContextAtCursor(editorInstance);
            //onHelpContextChange(context ? {type: context.closestMappingType} : null);
          }
        },
        onBlur: (editorInstance: CodeMirror.Editor) => {
          performLint(editorInstance);
        },
        onKeyUp: (editorInstance: CodeMirror.Editor, event: Event) => {
          if (event instanceof KeyboardEvent && AUTO_COMPLETE_AFTER_KEY.test(event.key)) {
            editorInstance.execCommand('autocomplete');
          }
        },
      };
    }, []);

    // Unfortunately, CodeMirror is too intense to be simulated in the JSDOM "virtual" DOM.
    // Until we run tests against something like selenium, trying to render the editor in
    // tests have to stop here.
    if (process.env.NODE_ENV === 'test') {
      return <span />;
    }

    return (
      <div style={{flex: 1, position: 'relative'}}>
        <ConfigEditorStyle />
        <StyledRawCodeMirror
          value={configCode}
          theme={['config-editor']}
          options={options}
          handlers={handlers}
        />
      </div>
    );
  },
);

BlueprintConfigEditor.displayName = 'NewConfigEditor';
