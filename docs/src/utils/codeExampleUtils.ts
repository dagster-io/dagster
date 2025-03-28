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
