import path from 'path';
import fs from 'fs';

const PATH_TO_EXAMPLES = path.resolve('../examples');
const CODE_EXAMPLE_START_REGEX = /<(CodeExample|CliInvocationExample)/g;
const CODE_EXAMPLE_PROP_REGEX = /([a-zA-Z0-9]+)={?["`](.*?)["`]}?/g;

export type CodeExampleFormatProps = {
  lineStart?: string;
  lineEnd?: string;
  startAfter?: string;
  endBefore?: string;
  dedent?: string;
};

export async function inlineCodeExampleFileReferences(content: string) {
  const codeExampleMatches: {
    reactText: string;
    props: CodeExampleFormatProps & {
      path?: string;
      contents?: string;
      language?: string;
    };
  }[] = [];

  let foundMatch: RegExpExecArray | null;
  while ((foundMatch = CODE_EXAMPLE_START_REGEX.exec(content)) !== null) {
    let reactText = content.slice(foundMatch.index);
    const reactEnd = /\/>/.exec(reactText)!;
    reactText = reactText.slice(0, reactEnd.index + reactEnd.length + 1);

    // Parse key=value props that were passed to the component. We use a separate
    // regexp to do this because they may appear in any order.
    const propsText = reactText.slice(foundMatch.length).replace(/\n/g, ' ');
    const props: {[key: string]: string} = {};
    let propMatch: RegExpExecArray | null;
    while ((propMatch = CODE_EXAMPLE_PROP_REGEX.exec(propsText)) !== null) {
      const [, propKey, propValue] = propMatch;
      props[propKey] = propValue;
    }

    codeExampleMatches.push({reactText, props});
  }

  for (const {reactText, props} of codeExampleMatches) {
    const language = (props.language ?? props.path?.endsWith('.py')) ? 'python' : undefined;

    if (props.contents) {
      // For CliInvocationExample
      content = content.replace(reactText, asCodeBlock(props.contents.trim(), language));
    } else if (props.path) {
      // For CliInvocationExample, CodeExample
      const contents = await fs.promises.readFile(path.join(PATH_TO_EXAMPLES, props.path), 'utf8');
      const trimmed = trimCodeExample(contents, props);
      content = content.replace(reactText, asCodeBlock(trimmed, language));
    }
  }

  return content;
}

// Private

const asCodeBlock = (code: string, language = '') =>
  `\`\`\`${language || ''}\n${code.trim()}\n\`\`\``;

/**
 * This function and the helpers below apply the <CodeExample /> props to the loaded
 * content, trimming it and selecting the portion indicating by the props. This should
 * be kept in sync with CodeExample.tsx::processModule.
 */
function trimCodeExample(contents: string, props: CodeExampleFormatProps) {
  let lines = contents.split('\n');

  const lineStart = props.lineStart ? Number(props.lineStart) : undefined;
  const lineEnd = props.lineEnd ? Number(props.lineEnd) : undefined;
  const dedent = props.dedent ? Number(props.dedent) : undefined;
  const {startAfter, endBefore} = props;

  // limit to range of `lineStart` and `lineEnd`
  const lineStartIndex = lineStart && lineStart > 0 ? lineStart : 0;
  const lineEndIndex = lineEnd && lineEnd <= lines.length ? lineEnd : lines.length;

  // limit to range of `startAfter` and `endBefore`
  const startAfterIndex = startAfter
    ? lines.findIndex((line: string) => line.includes(startAfter)) + 1
    : 0;

  const endAfterIndex = endBefore
    ? lines.findIndex((line: string) => line.includes(endBefore))
    : lines.length;

  const ix1 = Math.max(lineStartIndex, startAfterIndex);
  const ix2 = Math.min(lineEndIndex, endAfterIndex);

  lines = lines.slice(ix1, ix2);

  lines = filterComments(lines);

  lines = trimMainBlock(lines);

  if (dedent && dedent > 0) {
    lines = dedentLines(lines, dedent);
  }

  return lines.join('\n');
}

/**
 * Removes content below the `if __name__` block for the given `lines`.
 */
export function trimMainBlock(lines: string[]): string[] {
  const mainIndex = lines.findIndex((line) => /^if\s*__name__\s*==\s*['"]__main__['"]:/.test(line));
  return mainIndex !== -1 ? lines.slice(0, mainIndex) : lines;
}

const IGNORED_COMMENT_TYPES = ['noqa', 'type: ignore', 'isort'];

/**
 * Filters specified comment types from lines.
 */
export function filterComments(lines: string[]): string[] {
  const commentPattern = new RegExp(`(\\s*?)#.*?(${IGNORED_COMMENT_TYPES.join('|')}).*?$`, 'g');
  return lines.map((line: string) => {
    return line.replace(commentPattern, '');
  });
}

/**
 * Reduce indentation of text given number of characters.
 */
export function dedentLines(lines: string[], dedentAmount: number): string[] {
  const regex = new RegExp(`^ {0,${dedentAmount}}`);
  return lines.map((line) => line.replace(regex, ''));
}
