import * as CodeMirror from 'codemirror';
import 'codemirror/addon/hint/show-hint';
import 'codemirror/addon/search/search';
import 'codemirror/addon/search/searchcursor';
import 'codemirror/addon/dialog/dialog';
import 'codemirror/addon/dialog/dialog.css';
import * as yaml from 'yaml';

import {ConfigEditorRunConfigSchemaFragment} from '../types/ConfigEditorRunConfigSchemaFragment';

interface IParseStateParent {
  key: string;
  indent: number;
  childKeys: string[];
}

enum ContainerType {
  Dict = 'dict',
  List = 'list',
}

interface IParseState {
  trailingSpace: boolean;
  inlineContainers: ContainerType[];
  escaped: boolean;
  inValue: boolean;
  inBlockLiteral: boolean;
  lastIndent: number;
  parents: IParseStateParent[];
}

// Helper methods that mutate parser state. These must return new JavaScript objects.
//
function parentsPoppingItemsDeeperThan(parents: IParseStateParent[], indent: number) {
  while (parents.length > 0 && parents[parents.length - 1].indent >= indent) {
    parents = parents.slice(0, parents.length - 1);
  }
  return parents;
}

function parentsAddingChildKeyToLast(parents: IParseStateParent[], key: string) {
  if (parents.length === 0) return [];

  const immediateParent = parents[parents.length - 1];
  return [
    ...parents.slice(0, parents.length - 1),
    {
      key: immediateParent.key,
      indent: immediateParent.indent,
      childKeys: [...immediateParent.childKeys, key],
    },
  ];
}

function parentsAddingChildKeyAtIndent(parents: IParseStateParent[], key: string, indent: number) {
  parents = parentsPoppingItemsDeeperThan(parents, indent);
  parents = parentsAddingChildKeyToLast(parents, key);
  parents = [...parents, {key, indent: indent, childKeys: []}];
  return parents;
}

const Constants = ['true', 'false', 'on', 'off', 'yes', 'no'];

export const RegExps = {
  KEYWORD: new RegExp('\\b((' + Constants.join(')|(') + '))$', 'i'),
  DICT_COLON: /^:\s*/,
  // eslint-disable-next-line no-useless-escape
  DICT_KEY: /^\s*(?:[,\[\]{}&*!|>'"%@`][^\s'":]|[^,\[\]{}#&*!|>'"%@`])[^# ,]*?(?=\s*:)/,
  // same as above, but to avoid clasifiyng "a" as a sub-dict in "value: a:b", we require whitespace after the colon
  // eslint-disable-next-line no-useless-escape
  DICT_KEY_IN_VALUE: /^\s*(?:[,\[\]{}&*!|>'"%@`][^\s'":]|[^,\[\]{}#&*!|>'"%@`])[^# ,]*?(?=\s*:\s+)/,
  QUOTED_STRING: /^('([^']|\\.)*'?|"([^"\\]|\\.)*"?)/,
  UNQUOTED_STRING: /^.*$/,
  // eslint-disable-next-line no-useless-escape
  BLOCKSTART_PIPE_OR_ARROW: /^\s*(\||\>)\s*/,
  // eslint-disable-next-line no-useless-escape
  NUMBER: /^\s*-?[0-9\.]+(?![0-9\.]*[^0-9.\s])\s?/,
  // eslint-disable-next-line no-useless-escape
  VARIABLE: /^\s*(\&|\*)[a-z0-9\._-]+\b/i,
};

CodeMirror.defineMode('yaml', () => {
  return {
    lineComment: '#',
    fold: 'indent',
    startState: (): IParseState => {
      return {
        trailingSpace: false,
        escaped: false,
        inValue: false,
        inBlockLiteral: false,
        inlineContainers: [],
        lastIndent: 0,
        parents: [],
      };
    },
    token: (stream, state: IParseState) => {
      const ch = stream.peek();

      // reset escape, indent and trailing
      const wasEscaped = state.escaped;
      const wasTrailingSpace = state.trailingSpace;
      const lastIndent = state.lastIndent;
      state.lastIndent = stream.indentation();
      state.escaped = false;
      state.trailingSpace = false;

      // whitespace
      const trailingSpace = stream.eatSpace();
      if (trailingSpace) {
        state.trailingSpace = true;
        return 'whitespace';
      }
      // escape
      if (ch === '\\') {
        state.escaped = true;
        stream.next();
        return null;
      }

      // comments
      // either beginning of the line or had whitespace before
      if (ch === '#' && (stream.sol() || wasTrailingSpace)) {
        stream.skipToEnd();
        return 'comment';
      }

      if (state.inBlockLiteral) {
        // continuation of a literal string that was started on a previous line
        if (stream.indentation() > lastIndent) {
          stream.skipToEnd();
          return 'string';
        }
        state.inBlockLiteral = false;
      }

      // array list item, value to follow
      if (stream.match(/-/)) {
        state.inValue = true;
        return 'meta';
      }

      // doc start / end
      if (stream.sol()) {
        state.inValue = false;
        state.parents = [];

        if (stream.match(/---/) || stream.match(/\.\.\./)) {
          return 'def';
        }
      }

      // Handle inline objects and arrays. These can be nested arbitrarily but we
      // don't currently support them spanning multiple lines.
      if (stream.match(/^(\{|\}|\[|\])/)) {
        if (ch === '{') {
          state.inlineContainers = [...state.inlineContainers, ContainerType.Dict];
          state.inValue = false;
        } else if (ch === '}') {
          state.inlineContainers = state.inlineContainers.slice(
            0,
            state.inlineContainers.length - 1,
          );
          state.parents = state.parents.slice(0, state.parents.length - 1);
          state.inValue = state.inlineContainers.length > 0;
        } else if (ch === '[') {
          state.inlineContainers = [...state.inlineContainers, ContainerType.List];
        } else if (ch === ']') {
          state.inlineContainers = state.inlineContainers.slice(
            0,
            state.inlineContainers.length - 1,
          );
          state.inValue = state.inlineContainers.length > 0;
        }
        state.trailingSpace = false;
        return 'meta';
      }

      // Handle inline separators. For dictionaries, we pop from value parsing state back to
      // key parsing state after a comma and unwind the parent stack.
      if (state.inlineContainers && !wasEscaped && ch === ',') {
        const current = state.inlineContainers[state.inlineContainers.length - 1];
        if (current === ContainerType.Dict) {
          state.parents = state.parents.slice(0, state.parents.length - 1);
          state.inValue = false;
        }
        stream.next();
        return 'meta';
      }

      // A `:` fragment starts value parsing mode if it is not the last character on the line
      if (stream.match(RegExps.DICT_COLON)) {
        state.inValue = !stream.eol();
        return 'meta';
      }

      // general strings
      if (stream.match(RegExps.QUOTED_STRING)) {
        return 'string';
      }

      // Handle dict key fragments. May be the first element on a line or nested within an inline
      // (eg: {a: 1, b: 2}). We add the new key to the current `parent` and push a new parent
      // in case the dict key has subkeys.
      if (!state.inValue) {
        const match = stream.match(RegExps.DICT_KEY);
        if (match) {
          const key = match[0];
          const keyIndent = stream.pos - key.length;
          state.parents = parentsAddingChildKeyAtIndent(state.parents, key, keyIndent);
          return 'atom';
        }
      }

      if (state.inValue) {
        let result = null;

        if (stream.match(RegExps.QUOTED_STRING)) {
          result = 'string';
        }
        if (stream.match(RegExps.BLOCKSTART_PIPE_OR_ARROW)) {
          state.inBlockLiteral = true;
          result = 'meta';
        }
        if (stream.match(RegExps.VARIABLE)) {
          result = 'variable-2';
        }
        if (stream.match(RegExps.NUMBER)) {
          result = 'number';
        }
        if (stream.match(RegExps.KEYWORD)) {
          result = 'keyword';
        }

        // Child dicts can start within a value if the user is creating a list
        const match = stream.match(RegExps.DICT_KEY_IN_VALUE);
        if (match) {
          const key = match[0];
          const keyIndent = stream.pos - key.length;
          state.inValue = false;
          state.parents = parentsAddingChildKeyAtIndent(state.parents, key, keyIndent);
          result = 'atom';
        }

        // "In YAML, you can write a string without quotes, if it doesn't have a special meaning.",
        // so if we can't match the content to any other type and we are inValue, we make it a string.
        // http://blogs.perl.org/users/tinita/2018/03/strings-in-yaml---to-quote-or-not-to-quote.html
        if (!result && stream.match(RegExps.UNQUOTED_STRING)) {
          result = 'string';
        }
        stream.eatSpace();

        // If after consuming the value and trailing spaces we're at the end of the
        // line, terminate the value and look for another key on the following line.
        if (stream.eol() && !state.inBlockLiteral) {
          state.inValue = false;
        }

        // If we can't identify the value, bail out and abort parsing the line
        if (!result) {
          stream.skipToEnd();
          state.inValue = false;
        }

        return result;
      }

      stream.skipToEnd();

      return null;
    },
  };
});

// TODO
// Uniquity of keys
// add colon
// add colon and return for composites

type CodemirrorLocation = {
  line: number;
  ch: number;
};

type CodemirrorHint = {
  render: (el: Element, self: any, data: any) => void;
  text: string;
  from: CodemirrorLocation;
  to: CodemirrorLocation;
};

type CodemirrorToken = CodeMirror.Token & {
  state: IParseState;
};

type FoundHint = {
  text: string;
  displayText: string;
};

CodeMirror.registerHelper(
  'hint',
  'yaml',
  (
    editor: any,
    options: {
      schema?: ConfigEditorRunConfigSchemaFragment;
    },
  ): {list: Array<CodemirrorHint>} => {
    if (!options.schema) return {list: []};

    const {
      cursor,
      context,
      token,
      start,
      searchString,
      prevToken,
    } = expandAutocompletionContextAtCursor(editor);
    if (!context) {
      return {list: []};
    }

    // Since writing meaningful tests for this functionality is difficult given a) no jsdom
    // support for APIs that codemirror uses (and so no way to use snapshot tests) and b) no
    // appetite (yet) for writing Selenium tests, we record here the manual tests used to verify
    // this logic. In what follows, | represents the position of the cursor and -> the transition
    // on accepting an autocomplete suggestion for `storage: filesystem:

    // st|
    // ->
    // storage:
    //   |

    // storage:|
    // ->
    // storage:
    //   filesystem:
    //     |

    // storage: |
    // ->
    // storage:
    //   filesystem:
    //     |

    // storage:  |
    // ->
    // storage:
    //   filesystem:
    //     |

    // storage:
    //   |
    // ->
    // storage:
    //   filesystem:
    //     |

    const isCompOrList = (key: string): boolean => {
      if (!options.schema) {
        return false;
      }
      // Using a lookup table here seems like a good idea
      // https://github.com/dagster-io/dagster/issues/1966
      const type = options.schema.allConfigTypes.find((t) => t.key === key);
      if (!type) {
        return false;
      }
      return type.__typename === 'ArrayConfigType' || type.__typename === 'CompositeConfigType';
    };

    const formatReplacement = (
      field: any,
      start: any,
      token: CodemirrorToken,
      prevToken: CodemirrorToken,
    ) => {
      let replacement = `${field.name}`;

      const isCompositeOrList = isCompOrList(field.configTypeKey);

      const tokenIsColon = token.string.startsWith(':');

      if (isCompositeOrList && tokenIsColon) {
        replacement = `\n${' '.repeat(prevToken.start + 2)}${field.name}:\n${' '.repeat(
          prevToken.start + 4,
        )}`;
      } else if (isCompositeOrList) {
        replacement = `${field.name}:\n${' '.repeat(start + 2)}`;
      } else if (tokenIsColon) {
        replacement = `\n${' '.repeat(prevToken.start + 2)}${field.name}`;
      }
      return replacement;
    };

    const buildSuggestion = (
      display: string,
      replacement: string,
      description: string | null,
    ): CodemirrorHint => ({
      text: replacement,
      render: (el) => {
        const div = document.createElement('div');
        div.textContent = display;
        if (description) {
          const docs = document.createElement('div');
          docs.innerText =
            description.length < 90 ? description : description.substr(0, 87) + '...';
          docs.style.opacity = '0.5';
          docs.style.overflow = 'hidden';
          docs.style.maxHeight = '33px';
          docs.style.maxWidth = '360px';
          docs.style.whiteSpace = 'normal';
          div.appendChild(docs);
        }
        el.appendChild(div);
      },
      from: {line: cursor.line, ch: start},
      to: {line: cursor.line, ch: token.end},
    });

    // Calculate if this is on a new-line child of a scalar union type, as an indication that we
    // should autocomplete the selector fields of the scalar union
    const isScalarUnionNewLine =
      context.type.__typename === 'ScalarUnionConfigType' && !prevToken.end;

    // The context will have available fields if the type is a composite config type OR a scalar
    // union type
    if (
      context.availableFields.length &&
      (context.type.__typename === 'CompositeConfigType' || isScalarUnionNewLine)
    ) {
      return {
        list: context.availableFields
          .filter((field) => field.name.startsWith(searchString))
          .map((field) =>
            buildSuggestion(
              field.name,
              formatReplacement(field, start, token, prevToken),
              field.description,
            ),
          ),
      };
    }

    // Completion of enum field values
    if (context.type.__typename === 'EnumConfigType') {
      const searchWithoutQuotes = searchString.startsWith('"')
        ? searchString.substr(1)
        : searchString;
      return {
        list: context.type.values
          .filter((val) => val.value.startsWith(searchWithoutQuotes))
          .map((val) => buildSuggestion(val.value, `"${val.value}"`, null)),
      };
    }

    // Completion of boolean field values
    if (context.type.__typename === 'RegularConfigType' && context.type.givenName === 'Bool') {
      return {
        list: ['True', 'False']
          .filter((val) => val.startsWith(searchString))
          .map((val) => buildSuggestion(val, val, null)),
      };
    }

    // Completion of Scalar Union field values, the union of the scalar suggestions and the
    // non-scalar suggestions
    const type = context.type;
    if (type.__typename === 'ScalarUnionConfigType') {
      const scalarType = options.schema.allConfigTypes.find((x) => x.key === type.scalarTypeKey);
      const nonScalarType = options.schema.allConfigTypes.find(
        (x) => x.key === type.nonScalarTypeKey,
      );
      let scalarSuggestions: CodemirrorHint[] = [];
      if (
        scalarType &&
        scalarType.__typename === 'RegularConfigType' &&
        scalarType.givenName === 'Bool'
      ) {
        scalarSuggestions = ['True', 'False']
          .filter((val) => val.startsWith(searchString))
          .map((val) => buildSuggestion(val, val, null));
      }
      let nonScalarSuggestions: CodemirrorHint[] = [];
      if (nonScalarType && nonScalarType.__typename === 'CompositeConfigType') {
        nonScalarSuggestions = nonScalarType.fields
          .filter((field) => field.name.startsWith(searchString))
          .map((field) =>
            buildSuggestion(
              field.name,
              formatReplacement(field, start, token, prevToken),
              field.description,
            ),
          );
      }

      return {list: [...scalarSuggestions, ...nonScalarSuggestions]};
    }

    return {list: []};
  },
);

/** Takes the pipeline schema and the YAML tokenizer state and returns the
 * type in scope and available (yet-to-be-used) fields
 * if it is a composite type.
 */
function findAutocompletionContext(
  schema: ConfigEditorRunConfigSchemaFragment | null,
  parents: IParseStateParent[],
  currentIndent: number,
) {
  parents = parents.filter(({indent}) => currentIndent > indent);
  const immediateParent = parents[parents.length - 1];

  if (!schema) {
    // Schema may still be loading
    return;
  }

  let type = schema.allConfigTypes.find((t) => t.key === schema.rootConfigType.key);
  if (!type || type.__typename !== 'CompositeConfigType') {
    return null;
  }

  let available = type.fields;
  let closestCompositeType = type;

  if (available && parents.length > 0) {
    for (const parent of parents) {
      const parentTypeDef = available.find(({name}) => parent.key === name);
      if (!parentTypeDef) {
        return null;
      }

      // The current composite type's available "fields" each only have a configType key.
      // The rest of the configType's information is in the top level schema.allConfigTypes
      // to avoid superlinear GraphQL response size.
      const parentConfigType = schema.allConfigTypes.find(
        (t) => t.key === parentTypeDef.configTypeKey,
      )!;
      let childTypeKey = parentConfigType.key;
      let childEntriesUnique = true;

      if (parentConfigType.__typename === 'ArrayConfigType') {
        childTypeKey = parentConfigType.typeParamKeys[0];
        childEntriesUnique = false;
      }

      type = schema.allConfigTypes.find((t) => t.key === childTypeKey);
      if (!type) {
        return null;
      }

      if (type.__typename === 'ScalarUnionConfigType') {
        available = [];
        const nonScalarTypeKey = type.nonScalarTypeKey;
        const nonScalarType = schema.allConfigTypes.find((x) => x.key === nonScalarTypeKey);
        if (nonScalarType && nonScalarType.__typename === 'CompositeConfigType') {
          available = nonScalarType.fields;
        }
      } else if (type.__typename === 'CompositeConfigType') {
        closestCompositeType = type;
        available = type.fields;

        if (parent === immediateParent && childEntriesUnique) {
          available = available.filter(
            (item) => immediateParent.childKeys.indexOf(item.name) === -1,
          );
        }
      } else {
        available = [];
      }
    }
  }

  return {type, closestCompositeType, availableFields: available};
}

// Find context for a fully- or partially- typed key or value in the YAML document
export function expandAutocompletionContextAtCursor(editor: any) {
  const schema: ConfigEditorRunConfigSchemaFragment = editor.options.hintOptions.schema;

  const cursor = editor.getCursor();
  const token: CodemirrorToken = editor.getTokenAt(cursor);
  const prevToken: CodemirrorToken = editor.getTokenAt({
    line: cursor.line,
    ch: token.start,
  });

  let searchString: string;
  let start: number;
  if (token.type === 'whitespace' || token.string.startsWith(':')) {
    searchString = '';
    start = token.end;
  } else {
    searchString = token.string;
    start = token.start;
  }

  // Takes the schema and the YAML tokenizer state and returns the
  // type in scope and available (yet-to-be-used) fields
  // if it is a composite type.
  return {
    start,
    cursor,
    searchString,
    token,
    prevToken,
    context: findAutocompletionContext(schema, token.state.parents, start),
  };
}

type CodemirrorLintError = {
  message: string;
  severity: 'error' | 'warning' | 'information' | 'hint';
  type: 'validation' | 'syntax' | 'deprecation';
  from: CodemirrorLocation;
  to: CodemirrorLocation;
};

export type YamlModeValidationResult =
  | {
      isValid: true;
    }
  | {
      isValid: false;
      errors: YamlModeValidationError[];
    };

export type YamlModeValidateFunction = (configJSON: object) => Promise<YamlModeValidationResult>;

export type YamlModeValidationError = {
  message: string;
  path: string[];
  reason: string;
};

CodeMirror.registerHelper('dagster-docs', 'yaml', (editor: any, pos: CodeMirror.Position) => {
  const token = editor.getTokenAt(pos);

  const schema: ConfigEditorRunConfigSchemaFragment = editor.options.hintOptions.schema;

  if (token.type !== 'atom') {
    return null;
  }

  const context = findAutocompletionContext(schema, token.state.parents, token.start);
  const match =
    context &&
    context.type.__typename === 'CompositeConfigType' &&
    context.type.fields.find((f) => f.name === token.string);

  if (match && match.description) {
    return match.description;
  }

  return null;
});

CodeMirror.registerHelper(
  'lint',
  'yaml',
  async (
    text: string,
    {checkConfig}: {checkConfig: YamlModeValidateFunction},
    editor: any,
  ): Promise<Array<CodemirrorLintError>> => {
    const codeMirrorDoc = editor.getDoc();

    // TODO: In some scenarios where every line yields an error `parseDocument` can take 1s+
    // and returns 20,000+ errors. The library does not have a "bail out" option but we need one.
    // However we can't switch libraries because we need the structured document model this returns.
    // (It's not just text parsed to plain JS objects.)
    const yamlDoc = yaml.parseDocument(text);
    const lints: Array<CodemirrorLintError> = [];
    const lintingTruncated = yamlDoc.errors.length > 10;
    let lastMarkLocation: CodeMirror.Position | undefined;

    yamlDoc.errors.slice(0, 10).forEach((error) => {
      const from = codeMirrorDoc.posFromIndex(
        error.source.range ? error.source.range.start : 0,
      ) as CodeMirror.Position;
      const to = codeMirrorDoc.posFromIndex(
        error.source.range ? error.source.range.end : Number.MAX_SAFE_INTEGER,
      ) as CodeMirror.Position;

      if (!lastMarkLocation || lastMarkLocation.line < from.line) {
        lastMarkLocation = from;
      }

      lints.push({
        message: error.message,
        severity: 'error',
        type: 'syntax',
        from,
        to,
      });
    });

    if (lintingTruncated && lastMarkLocation) {
      const nextLineLocation: CodeMirror.Position = {
        line: lastMarkLocation.line + 1,
        ch: 0,
      };
      lints.push({
        message: `${yamlDoc.errors.length - lints.length} more errors - bailed out.`,
        severity: 'warning',
        type: 'syntax',
        from: nextLineLocation,
        to: nextLineLocation,
      });
    }

    if (yamlDoc.errors.length === 0) {
      const json = yamlDoc.toJSON() || {};
      const validationResult = await checkConfig(json);
      if (!validationResult.isValid) {
        validationResult.errors.forEach((error) => {
          const lint = validationErrorToCodemirrorError(error, yamlDoc, codeMirrorDoc);
          if (lint) {
            lints.push(lint);
          }
        });
      }
    }

    return lints;
  },
);

export function validationErrorToCodemirrorError(
  error: YamlModeValidationError,
  yamlDoc: yaml.ast.Document,
  codeMirrorDoc: any,
): CodemirrorLintError | null {
  const part = error.reason === 'RUNTIME_TYPE_MISMATCH' ? 'value' : 'key';
  const range = findRangeInDocumentFromPath(yamlDoc, error.path, part);
  if (range === null) return null;
  return {
    message: error.message,
    severity: 'error',
    type: 'syntax',
    from: codeMirrorDoc.posFromIndex(range ? range.start : 0) as CodeMirror.Position,
    to: codeMirrorDoc.posFromIndex(
      range ? range.end : Number.MAX_SAFE_INTEGER,
    ) as CodeMirror.Position,
  };
}

export function findRangeInDocumentFromPath(
  doc: yaml.ast.Document,
  path: Array<string>,
  pathPart: 'key' | 'value',
): {start: number; end: number} | null {
  let node = nodeAtPath(doc, path);
  if (!node || !('type' in node) || node.type !== 'PAIR') return null;

  if (pathPart === 'value' && node.value) {
    node = node.value;
  } else {
    node = node.key;
  }

  if (node && node.range) {
    return {
      start: node.range[0],
      end: node.range[1],
    };
  } else {
    return null;
  }
}

function nodeAtPath(
  doc: yaml.ast.Document,
  path: Array<string>,
): yaml.ast.AstNode | yaml.ast.Pair | null {
  let node: any = doc.contents;
  for (let i = 0; i < path.length; i++) {
    const part = path[i];
    if (node && node.type && node.type === 'PAIR') {
      node = node.value;
    }

    if (node && node.type && (node.type === 'SEQ' || node.type === 'FLOW_SEQ')) {
      const index = Number.parseInt(part);
      if (!Number.isNaN(index)) {
        node = node.items[index];
      } else {
        return null;
      }
    } else if (node && node.type && (node.type === 'FLOW_MAP' || node.type === 'MAP')) {
      const item = node.items.find(({key}: {key: any}) => key.value === part);
      if (item && item.type && item.type === 'PAIR') {
        node = item;
      } else {
        return null;
      }
    } else {
      return null;
    }
  }

  return node;
}
