import * as CodeMirror from "codemirror";
import "codemirror/addon/hint/show-hint";
import * as yaml from "yaml";
import { Ajv } from "ajv";

interface IParseStateParent {
  key: string;
  indent: number;
  childKeys: string[];
}

interface IParseState {
  trailingSpace: boolean;
  inlineLists: number;
  inlinePairs: number;
  escaped: boolean;
  inDict: boolean;
  inDictValue: boolean;
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
  return parents
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
    }
  ]
}

const Constants = ["true", "false", "on", "off", "yes", "no"];

const RegExps = {
  KEYWORD: new RegExp("\\b((" + Constants.join(")|(") + "))$", "i"),
  DICT_COLON: /^:\s*/,
  DICT_KEY: /^\s*(?:[,\[\]{}&*!|>'"%@`][^\s'":]|[^,\[\]{}#&*!|>'"%@`])[^#]*?(?=\s*:($|\s))/,
  QUOTED_STRING: /^('([^']|\\.)*'?|"([^"]|\\.)*"?)/,
  BLOCKSTART_PIPE_OR_ARROW: /^\s*(\||\>)\s*/,
  NUMBER: /^\s*-?[0-9\.\,]+\s?$/,
  NUMBER_WITH_DICT_LOOKAHEAD: /^\s*-?[0-9\.]+\s?(?=(,|}))/,
  NUMBER_WITH_LIST_LOOKAHEAD: /^\s*-?[0-9\.]+\s?(?=(,|]))/,
  VARIABLE: /^\s*(\&|\*)[a-z0-9\._-]+\b/i
}

CodeMirror.defineMode("yaml", () => {
  return {
    lineComment: "#",
    fold: "indent",
    startState: (): IParseState => {
      return {
        trailingSpace: false,
        escaped: false,
        inDict: false,
        inDictValue: false,
        inBlockLiteral: false,
        inlineLists: 0,
        inlinePairs: 0,
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
        state.inDictValue = true;
        return "meta";
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

      // inline list / dict eg: `key: {a: 1, b: 2}`
      if (stream.match(/^(\{|\}|\[|\])/)) {
        if (ch == "{") {
          state.inlinePairs++;
        } else if (ch == "}") {
          state.inlinePairs--;
        } else if (ch == "[") {
          state.inlineLists++;
        } else {
          state.inDictValue = false;
          state.inlineLists--;
        }
        state.trailingSpace = false;
        return "meta";
      }

      // list seperator
      if (state.inlineLists > 0 && !wasEscaped && ch == ",") {
        stream.next();
        return "meta";
      }

      // pairs seperator
      if (state.inlinePairs > 0 && !wasEscaped && ch == ",") {
        state.inDict = false;
        state.inDictValue = false;
        stream.next();
        return "meta";
      }

      if (!state.inDictValue) {
        const match = stream.match(RegExps.DICT_KEY)
        if (match) {
          const key = match[0];
          state.inDict = true;
          state.parents = parentsPoppingItemsDeeperThan(state.parents, stream.indentation())
          state.parents = parentsAddingChildKeyToLast(state.parents, key)
          state.parents = [
            ...state.parents,
            { key: key, indent: state.lastIndent, childKeys: [] }
          ];
          return "atom";
        }
      }

      if (state.inDict && stream.match(RegExps.DICT_COLON)) {
        state.inDictValue = true;
        return "meta";
      }

      // dicts
      if (state.inDictValue) {
        let result = null;
        /* strings */
        if (stream.match(RegExps.QUOTED_STRING)) {
          result = "string";
        }

        if (stream.match(RegExps.BLOCKSTART_PIPE_OR_ARROW)) {
          state.inBlockLiteral = true;
          result = "meta";
        }
        /* references */
        if (stream.match(RegExps.VARIABLE)) {
          result = "variable-2";
        }
        /* numbers */
        if (state.inlinePairs == 0 && stream.match(RegExps.NUMBER)) {
          result = "number";
        }
        if (
          state.inlinePairs > 0 &&
          stream.match(RegExps.NUMBER_WITH_DICT_LOOKAHEAD)
        ) {
          result = "number";
        }
        if (
          state.inlineLists > 0 &&
          stream.match(RegExps.NUMBER_WITH_LIST_LOOKAHEAD)
        ) {
          result = "number";
          return result; // remain inDictValue until we reach `]`
        }
        /* keywords */
        if (stream.match(RegExps.KEYWORD)) {
          result = "keyword";
        }

        state.inDictValue = false;
        return result;
      }

      // general strings
      if (stream.match(RegExps.QUOTED_STRING)) {
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
  parents: IParseStateParent[],
  currentIndent: number
): FoundHint[] {
  parents = parents.filter(({ indent }) => currentIndent > indent);

  let available = typeConfig.environment;

  if (available && parents.length > 0) {
    for (const parent of parents) {
      const parentTypeDef = available.find(({ name }) => parent.key === name);
      if (
        parentTypeDef &&
        parentTypeDef.typeName &&
        typeConfig.types[parentTypeDef.typeName]
      ) {
        available = typeConfig.types[parentTypeDef.typeName];
      } else {
        return [];
      }
    }

    const immediateParent = parents[parents.length - 1]
    if (immediateParent) {
      available = available.filter(item => 
        immediateParent.childKeys.indexOf(item.name) === -1
      )
    }
  }

  return available.map(item => ({
    text: item.name,
    hasChildren: item.typeName ? item.typeName in typeConfig.types : false
  }))
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
