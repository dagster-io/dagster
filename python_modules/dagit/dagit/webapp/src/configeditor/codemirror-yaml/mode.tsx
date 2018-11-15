import * as CodeMirror from "codemirror";
import "codemirror/addon/hint/show-hint";
import * as yaml from "yaml";
import { Ajv } from "ajv";

interface IParseState {
  trailingSpace: boolean;
  inlineLists: number;
  inlinePairs: number;
  escaped: boolean;
  inDict: boolean;
  inDictValue: boolean;
  inLiteral: boolean;
  lastIndent: number;
  parents: Array<{ key: string; indent: number }>;
  keysAtLevel: { [indent: number]: Array<string> };
}

CodeMirror.defineMode("yaml", () => {
  const constants = ["true", "false", "on", "off", "yes", "no"];
  const keywordRegex = new RegExp("\\b((" + constants.join(")|(") + "))$", "i");

  return {
    lineComment: "#",
    fold: "indent",
    startState: () => {
      const state: IParseState = {
        trailingSpace: false,
        escaped: false,
        inDict: false,
        inDictValue: false,
        inLiteral: false,
        inlineLists: 0,
        inlinePairs: 0,
        lastIndent: 0,
        parents: [],
        keysAtLevel: {}
      };
      return state;
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
      // list
      if (stream.match(/-/)) {
        return "meta";
      }

      if (state.inLiteral && stream.indentation() > lastIndent) {
        // literal strings
        stream.skipToEnd();
        return "string";
      } else if (state.inLiteral) {
        state.inLiteral = false;
      }

      // doc start / end
      if (stream.sol()) {
        state.inDict = false;
        state.inDictValue = false;
        state.parents = [];

        if (stream.match(/---/) || stream.match(/\.\.\./)) {
          state.inDict = false;
          return "def";
        }
      }

      // inline list / dict
      if (stream.match(/^(\{|\}|\[|\])/)) {
        if (ch == "{") {
          state.inlinePairs++;
        } else if (ch == "}") {
          state.inlinePairs--;
        } else if (ch == "[") {
          state.inlineLists++;
        } else {
          state.inlineLists--;
        }
        state.trailingSpace = false;
        return "meta";
      }

      if (state.inlineLists > 0 && !wasEscaped && ch == ",") {
        stream.next();
        return "meta";
      }

      if (state.inlinePairs > 0 && !wasEscaped && ch == ",") {
        state.inDict = false;
        state.inDictValue = false;
        stream.next();
        return "meta";
      }

      /* pairs (associative arrays) -> key */
      if (!state.inDictValue) {
        const values = stream.match(
          /^\s*(?:[,\[\]{}&*!|>'"%@`][^\s'":]|[^,\[\]{}#&*!|>'"%@`])[^#]*?(?=\s*:($|\s))/
        );
        if (values) {
          const value = values[0];
          state.inDict = true;
          while (
            state.parents.length > 0 &&
            state.parents[state.parents.length - 1].indent >=
              stream.indentation()
          ) {
            state.parents = state.parents.slice(0, state.parents.length - 1);
          }
          state.parents = [
            ...state.parents,
            { key: value, indent: state.lastIndent }
          ];
          return "atom";
        }
      }

      if (state.inDict && stream.match(/^:\s*/)) {
        state.inDictValue = true;
        return "meta";
      }

      // dicts
      if (state.inDictValue) {
        let result = null;
        // strings
        if (stream.match(/^('([^']|\\.)*'?|"([^"]|\\.)*"?)/)) {
          result = "string";
        }

        if (stream.match(/^\s*(\||\>)\s*/)) {
          state.inLiteral = true;
          result = "meta";
        }
        /* references */
        if (stream.match(/^\s*(\&|\*)[a-z0-9\._-]+\b/i)) {
          result = "variable-2";
        }
        /* numbers */
        if (state.inlinePairs == 0 && stream.match(/^\s*-?[0-9\.\,]+\s?$/)) {
          result = "number";
        }
        if (
          state.inlinePairs > 0 &&
          stream.match(/^\s*-?[0-9\.\,]+\s?(?=(,|}))/)
        ) {
          result = "number";
        }
        /* keywords */
        if (stream.match(keywordRegex)) {
          result = "keyword";
        }

        state.inDictValue = false;
        return result;
      }

      // general strings
      if (stream.match(/^('([^']|\\.)*'?|"([^"]|\\.)*"?)/)) {
        return "string";
      }

      stream.skipToEnd();
      while (
        state.parents.length > 0 &&
        state.parents[state.parents.length - 1].indent >= stream.indentation()
      ) {
        state.parents = state.parents.slice(0, state.parents.length - 1);
      }

      return null;
    }
  };
});

export type TypeConfig = {
  environment: Array<{ name: string; typeName?: string }>;
  types: {
    [name: string]: Array<{
      name: string;
      typeName: string;
    }>;
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
  parents: Array<{ key: string; indent: number }>,
  currentIndent: number
): Array<FoundHint> {
  parents = parents.filter(({ indent }) => currentIndent > indent);
  let currentType = typeConfig.environment;
  if (currentType && parents.length > 0) {
    for (const parent of parents) {
      const currentTypeDef = currentType.find(
        ({ name }: { name: string }) => parent.key === name
      );
      if (
        currentTypeDef &&
        currentTypeDef.typeName &&
        typeConfig.types[currentTypeDef.typeName]
      ) {
        currentType = typeConfig.types[currentTypeDef.typeName];
      } else {
        return [];
      }
    }
  }

  return currentType.map(
    ({ name, typeName }: { name: string; typeName: string }) => ({
      text: name,
      hasChildren: typeName in typeConfig.types
    })
  );
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
};

CodeMirror.registerHelper(
  "lint",
  "yaml",
  async (
    text: string,
    { lintJson }: { lintJson: LintJson },
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
      const validationResult = await lintJson(json);
      if (!validationResult.isValid) {
        validationResult.errors.forEach(error => {
          const range = findRangeInDocumentFromPath(doc, error.path);
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
  path: Array<string>
): { start: number; end: number } | null {
  let node: any = nodeAtPath(doc, path);
  if (node && node.type && node.type === "PAIR") {
    node = node.key;
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
