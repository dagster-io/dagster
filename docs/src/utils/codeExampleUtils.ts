/**
 * Removes content below the `if __name__` block for the given `lines`.
 */
export function trimMainBlock(lines: string[]): string[] {
  const mainIndex = lines.findIndex((line) => /^if\s*__name__\s*==\s*['"]__main__['"]:/.test(line));
  return mainIndex !== -1 ? lines.slice(0, mainIndex) : lines;
}

/**
 * Filters `noqa` comments from lines.
 */
export function filterNoqaComments(lines: string[]): string[] {
  return lines.map((line: string) => {
    return line.replaceAll(/#.*?noqa.*?$/g, '');
  });
}

