import * as CodeMirror from "codemirror";
import "codemirror/addon/hint/show-hint";
import * as yaml from "yaml";

interface IParseStateParent {
  key: string;
  indent: number;
  childKeys: string[];
}

enum ContainerType {
  Dict = "dict",
  List = "list"
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
function parentsPoppingItemsDeeperThan(
  parents: IParseStateParent[],
  indent: number
) {
  while (parents.length > 0 && parents[parents.length - 1].indent >= indent) {
    parents = parents.slice(0, parents.length - 1);
  }
  return parents;
}

function parentsAddingChildKeyToLast(
  parents: IParseStateParent[],
  key: string
) {
  if (parents.length === 0) return [];

  const immediateParent = parents[parents.length - 1];
  return [
    ...parents.slice(0, parents.length - 1),
    {
      key: immediateParent.key,
      indent: immediateParent.indent,
      childKeys: [...immediateParent.childKeys, key]
    }
  ];
}

function parentsAddingChildKeyAtIndent(
  parents: IParseStateParent[],
  key: string,
  indent: number
) {
  parents = parentsPoppingItemsDeeperThan(parents, indent);
  parents = parentsAddingChildKeyToLast(parents, key);
  parents = [...parents, { key, indent: indent, childKeys: [] }];
  return parents;
}

const Constants = ["true", "false", "on", "off", "yes", "no"];

const RegExps = {
  KEYWORD: new RegExp("\\b((" + Constants.join(")|(") + "))$", "i"),
  DICT_COLON: /^:\s*/,
  DICT_KEY: /^\s*(?:[,\[\]{}&*!|>'"%@`][^\s'":]|[^,\[\]{}#&*!|>'"%@`])[^# ,]*?(?=\s*:)/,
  QUOTED_STRING: /^('([^']|\\.)*'?|"([^"]|\\.)*"?)/,
  BLOCKSTART_PIPE_OR_ARROW: /^\s*(\||\>)\s*/,
  NUMBER: /^\s*-?[0-9\.]+\s?/,
  VARIABLE: /^\s*(\&|\*)[a-z0-9\._-]+\b/i
};

CodeMirror.defineMode("yaml", () => {
  return {
    lineComment: "#",
    fold: "indent",
    startState: (): IParseState => {
      return {
        trailingSpace: false,
        escaped: false,
        inValue: false,
        inBlockLiteral: false,
        inlineContainers: [],
        lastIndent: 0,
        parents: []
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
        return "whitespace";
      }
      // escape
      if (ch === "\\") {
        state.escaped = true;
        stream.next();
        return null;
      }

      // comments
      // either beginning of the line or had whitespace before
      if (ch === "#" && (stream.sol() || wasTrailingSpace)) {
        stream.skipToEnd();
        return "comment";
      }

      if (state.inBlockLiteral) {
        // continuation of a literal string that was started on a previous line
        if (stream.indentation() > lastIndent) {
          stream.skipToEnd();
          return "string";
        }
        state.inBlockLiteral = false;
      }

      // array list item, value to follow
      if (stream.match(/-/)) {
        state.inValue = true;
        return "meta";
      }

      // doc start / end
      if (stream.sol()) {
        state.inValue = false;
        state.parents = [];

        if (stream.match(/---/) || stream.match(/\.\.\./)) {
          return "def";
        }
      }

      // Handle inline objects and arrays. These can be nested arbitrarily but we
      // don't currently support them spanning multiple lines.
      if (stream.match(/^(\{|\}|\[|\])/)) {
        if (ch == "{") {
          state.inlineContainers = [
            ...state.inlineContainers,
            ContainerType.Dict
          ];
          state.inValue = false;
        } else if (ch == "}") {
          state.inlineContainers = state.inlineContainers.slice(
            0,
            state.inlineContainers.length - 1
          );
          state.parents = state.parents.slice(0, state.parents.length - 1);
          state.inValue = state.inlineContainers.length > 0;
        } else if (ch == "[") {
          state.inlineContainers = [
            ...state.inlineContainers,
            ContainerType.List
          ];
        } else if (ch == "]") {
          state.inlineContainers = state.inlineContainers.slice(
            0,
            state.inlineContainers.length - 1
          );
          state.inValue = state.inlineContainers.length > 0;
        }
        state.trailingSpace = false;
        return "meta";
      }

      // Handle inline separators. For dictionaries, we pop from value parsing state back to
      // key parsing state after a comma and unwind the parent stack.
      if (state.inlineContainers && !wasEscaped && ch == ",") {
        const current =
          state.inlineContainers[state.inlineContainers.length - 1];
        if (current === ContainerType.Dict) {
          state.parents = state.parents.slice(0, state.parents.length - 1);
          state.inValue = false;
        }
        stream.next();
        return "meta";
      }

      // A `:` fragment starts value parsing mode if it is not the last character on the line
      if (stream.match(RegExps.DICT_COLON)) {
        state.inValue = !stream.eol();
        return "meta";
      }

      // Handle dict key fragments. May be the first element on a line or nested within an inline
      // (eg: {a: 1, b: 2}). We add the new key to the current `parent` and push a new parent
      // in case the dict key has subkeys.
      if (!state.inValue) {
        const match = stream.match(RegExps.DICT_KEY);
        if (match) {
          const key = match[0];
          const keyIndent = stream.pos - key.length;
          state.parents = parentsAddingChildKeyAtIndent(
            state.parents,
            key,
            keyIndent
          );
          return "atom";
        }
      }

      if (state.inValue) {
        let result = null;

        if (stream.match(RegExps.QUOTED_STRING)) {
          result = "string";
        }
        if (stream.match(RegExps.BLOCKSTART_PIPE_OR_ARROW)) {
          state.inBlockLiteral = true;
          result = "meta";
        }
        if (stream.match(RegExps.VARIABLE)) {
          result = "variable-2";
        }
        if (stream.match(RegExps.NUMBER)) {
          result = "number";
        }
        if (stream.match(RegExps.KEYWORD)) {
          result = "keyword";
        }

        // Child dicts can start within a value if the user is creating a list
        const match = stream.match(RegExps.DICT_KEY);
        if (match) {
          const key = match[0];
          const keyIndent = stream.pos - key.length;
          state.inValue = false;
          state.parents = parentsAddingChildKeyAtIndent(
            state.parents,
            key,
            keyIndent
          );
          result = "atom";
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

      // general strings
      if (stream.match(RegExps.QUOTED_STRING)) {
        return "string";
      }

      stream.skipToEnd();

      return null;
    }
  };
});

export type TypeConfig = {
  rootTypeKey: string;
  types: {
    [key: string]: {
      fields: Array<{
        name: string;
        configType: {
          __typename: string;
          isList: boolean;
          isNullable: boolean;
          key: string;
          name: string | null;
          ofType?: {
            key: string
          };
        };
      }>;
    };
  };
};

// TODO
// Uniquity of keys
// add colon
// add colon and return for composites

type CodemirrorLocation = {
  line: number;
  ch: number;
};

type CodemirrorHint = {
  displayText: string;
  text: string;
  from: CodemirrorLocation;
  to: CodemirrorLocation;
};

type CodemirrorToken = {
  string: string;
  start: number;
  end: number;
  type: string;
  state: IParseState;
};

type FoundHint = {
  text: string;
  hasChildren: boolean;
};

CodeMirror.registerHelper(
  "hint",
  "yaml",
  (
    editor: any,
    options: { typeConfig: TypeConfig }
  ): { list: Array<CodemirrorHint> } => {
    const cur = editor.getCursor();
    const token: CodemirrorToken = editor.getTokenAt(cur);
    let searchString;
    let start;
    if (token.type === "whitespace") {
      searchString = "";
      start = token.end;
    } else {
      searchString = token.string;
      start = token.start;
    }

    let list: Array<FoundHint> = findAutocomplete(
      options.typeConfig,
      token.state.parents,
      start
    );

    return {
      list: processToHint(list, searchString, start, token.end, cur.line)
    };
  }
);

function processToHint(
  list: Array<FoundHint>,
  tokenString: string,
  tokenStart: number,
  tokenEnd: number,
  line: number
): Array<CodemirrorHint> {
  const result: Array<CodemirrorHint> = [];
  for (const hint of list) {
    if (hint.text.startsWith(tokenString)) {
      let text;
      if (hint.hasChildren) {
        text = `${hint.text}:\n${" ".repeat(tokenStart + 2)}`;
      } else {
        text = `${hint.text}: `;
      }
      result.push({
        displayText: hint.text,
        text: text,
        from: {
          line: line,
          ch: tokenStart
        },
        to: {
          line: line,
          ch: tokenEnd
        }
      });
    }
  }
  return result;
}

function findAutocomplete(
  typeConfig: TypeConfig,
  parents: IParseStateParent[],
  currentIndent: number
): FoundHint[] {
  parents = parents.filter(({ indent }) => currentIndent > indent);
  const immediateParent = parents[parents.length - 1];

  let available = typeConfig.types[typeConfig.rootTypeKey].fields;

  if (available && parents.length > 0) {
    for (const parent of parents) {
      const parentTypeDef = available.find(({ name }) => parent.key === name);

      if (!parentTypeDef) {
        return [];
      }

      let childTypeKey = parentTypeDef.configType.key;
      let childEntriesUnique = true;

      if (parentTypeDef.configType.isList) {
        // ofType guaranteed to have value in the List case
        // better way to enforce this?
        if (parentTypeDef.configType.ofType) {
          childTypeKey = parentTypeDef.configType.ofType.key
          childEntriesUnique = false;
        }
      }

      let childType = typeConfig.types[childTypeKey];
      available = childType && childType.fields;
      if (!available) {
        console.warn(`No type config is available for ${childTypeKey}`);
        return [];
      }

      if (parent === immediateParent && childEntriesUnique) {
        available = available.filter(
          item => immediateParent.childKeys.indexOf(item.name) === -1
        );
      }
    }
  }

  return available.map(item => ({
    text: item.name,
    hasChildren: item.configType.name
      ? item.configType.name in typeConfig.types
      : false
  }));
}

type CodemirrorLintError = {
  message: string;
  severity: "error" | "warning" | "information" | "hint";
  type: "validation" | "syntax" | "deprecation";
  from: CodemirrorLocation;
  to: CodemirrorLocation;
};

export type ValidationResult =
  | {
      isValid: true;
    }
  | {
      isValid: false;
      errors: Array<ValidationError>;
    };

export type LintJson = (json: any) => Promise<ValidationResult>;

type ValidationError = {
  message: string;
  path: Array<string>;
  reason: string;
};

CodeMirror.registerHelper(
  "lint",
  "yaml",
  async (
    text: string,
    { checkConfig }: { checkConfig: LintJson },
    editor: any
  ): Promise<Array<CodemirrorLintError>> => {
    const codeMirrorDoc = editor.getDoc();
    const docs = yaml.parseAllDocuments(text);
    if (docs.length === 0) {
      return [];
    }
    // Assumption
    const doc = docs[0];
    const lints: Array<CodemirrorLintError> = [];
    doc.errors.forEach(error => {
      lints.push({
        message: error.message,
        severity: "error",
        type: "syntax",
        from: codeMirrorDoc.posFromIndex(
          error.source.range ? error.source.range.start : 0
        ) as any,
        to: codeMirrorDoc.posFromIndex(
          error.source.range ? error.source.range.end : Number.MAX_SAFE_INTEGER
        ) as any
      });
    });

    if (doc.errors.length === 0) {
      const json = doc.toJSON();
      const validationResult = await checkConfig(json);
      if (!validationResult.isValid) {
        validationResult.errors.forEach(error => {
          const part =
            error.reason === "RUNTIME_TYPE_MISMATCH" ? "value" : "key";
          const range = findRangeInDocumentFromPath(doc, error.path, part);
          lints.push({
            message: error.message,
            severity: "error",
            type: "syntax",
            from: codeMirrorDoc.posFromIndex(range ? range.start : 0) as any,
            to: codeMirrorDoc.posFromIndex(
              range ? range.end : Number.MAX_SAFE_INTEGER
            ) as any
          });
        });
      }
    }

    return lints;
  }
);

function findRangeInDocumentFromPath(
  doc: yaml.ast.Document,
  path: Array<string>,
  pathPart: "key" | "value"
): { start: number; end: number } | null {
  let node: any = nodeAtPath(doc, path);
  if (node && node.type && node.type === "PAIR") {
    node = node[pathPart];
  }
  if (node && node.range) {
    return {
      start: node.range[0],
      end: node.range[1]
    };
  } else {
    return null;
  }
}

function nodeAtPath(
  doc: yaml.ast.Document,
  path: Array<string>
): yaml.ast.Node | yaml.ast.Pair | null {
  let node: any = doc.contents;
  for (let i = 0; i < path.length; i++) {
    const part = path[i];
    if (node && node.type && node.type === "PAIR") {
      node = node.value;
    }

    if (
      node &&
      node.type &&
      (node.type === "SEQ" || node.type === "FLOW_SEQ")
    ) {
      const index = Number.parseInt(part);
      if (!Number.isNaN(index)) {
        node = node.items[index];
      } else {
        return null;
      }
    } else if (
      node &&
      node.type &&
      (node.type === "FLOW_MAP" || node.type === "MAP")
    ) {
      const item = node.items.find(
        ({ key }: { key: any }) => key.value === part
      );
      if (item && item.type && item.type === "PAIR") {
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
