import * as CodeMirror from "codemirror";
import "codemirror/addon/hint/show-hint";
import * as yaml from "yaml";
import { ConfigEditorPipelineFragment } from "../types/ConfigEditorPipelineFragment";

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

type CodemirrorToken = {
  string: string;
  start: number;
  end: number;
  type: string;
  state: IParseState;
};

type FoundHint = {
  text: string;
  displayText: string;
};

CodeMirror.registerHelper(
  "hint",
  "yaml",
  (
    editor: any,
    options: { pipeline: ConfigEditorPipelineFragment }
  ): { list: Array<CodemirrorHint> } => {
    const cur = editor.getCursor();
    const token: CodemirrorToken = editor.getTokenAt(cur);

    let searchString: string;
    let start: number;
    if (token.type === "whitespace" || token.string.startsWith(":")) {
      searchString = "";
      start = token.end;
    } else {
      searchString = token.string;
      start = token.start;
    }

    // Takes the pipeline and the YAML tokenizer state and returns the
    // pipeline type in scope and available (yet-to-be-used) fields
    // if it is a composite type.
    const context = findAutocompletionContext(
      options.pipeline,
      token.state.parents,
      start
    );

    const shouldAddTrailingNewline = (type: { __typename: string }) =>
      type.__typename === "ListConfigType" ||
      type.__typename == "CompositeConfigType";

    const buildSuggestion = (
      display: string,
      replacement: string,
      description: string | null
    ): CodemirrorHint => ({
      text: replacement,
      render: (el, self, data) => {
        const div = document.createElement("div");
        div.textContent = display;
        if (description) {
          const docs = document.createElement("div");
          docs.innerText =
            description.length < 90
              ? description
              : description.substr(0, 87) + "...";
          docs.style.opacity = "0.5";
          docs.style.overflow = "hidden";
          docs.style.maxHeight = "33px";
          docs.style.maxWidth = "360px";
          docs.style.whiteSpace = "normal";
          div.appendChild(docs);
        }
        el.appendChild(div);
      },
      from: { line: cur.line, ch: start },
      to: { line: cur.line, ch: token.end }
    });

    // Completion of composite field keys
    if (context && context.availableFields.length) {
      return {
        list: context.availableFields
          .filter(field => field.name.startsWith(searchString))
          .map(field =>
            buildSuggestion(
              field.name,
              shouldAddTrailingNewline(field.configType)
                ? `${field.name}:\n${" ".repeat(start + 2)}`
                : `${field.name}: `,
              field.description
            )
          )
      };
    }

    // Completion of enum field values
    if (context && context.type.__typename === "EnumConfigType") {
      if (searchString.startsWith('"')) {
        searchString = searchString.substr(1);
      }
      return {
        list: context.type.values
          .filter(val => val.value.startsWith(searchString))
          .map(val => buildSuggestion(val.value, `"${val.value}"`, null))
      };
    }

    return { list: [] };
  }
);

function findAutocompletionContext(
  pipeline: ConfigEditorPipelineFragment,
  parents: IParseStateParent[],
  currentIndent: number
) {
  parents = parents.filter(({ indent }) => currentIndent > indent);
  const immediateParent = parents[parents.length - 1];

  let type = pipeline.configTypes.find(
    t => t.key === pipeline.environmentType.key
  );
  if (!type || type.__typename !== "CompositeConfigType") {
    return null;
  }

  let available = type.fields;

  if (available && parents.length > 0) {
    for (const parent of parents) {
      const parentTypeDef = available.find(({ name }) => parent.key === name);

      if (!parentTypeDef) {
        return null;
      }

      let childTypeKey = parentTypeDef.configType.key;
      let childEntriesUnique = true;

      if (parentTypeDef.configType.__typename === "ListConfigType") {
        childTypeKey = parentTypeDef.configType.ofType.key;
        childEntriesUnique = false;
      }

      type = pipeline.configTypes.find(t => t.key === childTypeKey);
      if (!type) {
        return null;
      }

      if (type.__typename !== "CompositeConfigType") {
        available = [];
      } else if (parent === immediateParent && childEntriesUnique) {
        available = type.fields.filter(
          item => immediateParent.childKeys.indexOf(item.name) === -1
        );
      } else {
        available = type.fields;
      }
    }
  }

  return { type, availableFields: available };
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

CodeMirror.registerHelper("dagster-docs", "yaml", (editor: any, pos: any) => {
  const pipeline = editor.options.hintOptions
    .pipeline as ConfigEditorPipelineFragment;
  const token: CodemirrorToken = editor.getTokenAt(pos);

  if (token.type !== "atom") {
    return null;
  }

  // Takes the pipeline and the YAML tokenizer state and returns the
  // pipeline type in scope and available (yet-to-be-used) fields
  // if it is a composite type.
  const context = findAutocompletionContext(
    pipeline,
    token.state.parents,
    token.start
  );

  const match =
    context &&
    context.type.__typename == "CompositeConfigType" &&
    context.type.fields.find(f => f.name === token.string);

  if (match && match.description) {
    return match.description;
  }

  return null;
});

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
  if (
    node &&
    node.type &&
    node.type === "PAIR" &&
    pathPart === "value" &&
    node.value
  ) {
    node = node.value;
  } else {
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
