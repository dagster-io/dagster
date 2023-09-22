const SPLIT_PATTERN = /\r?\n/;
const JOIN_PATTERN = '\n';
const MYPY_IGNORE = '# type: ignore';
/**
 * Use this method to apply a limit for file snippets generated
 * using the ::literalinclude directive
 *
 * Line ranges can be specified with the `fromTo` parameter using Sphinx syntax.
 * @see parseLineNumbersToSet
 *
 * startAfter and endBefore are used together or individually to select a line range using text
 * markers within the content itself. Take the following source content as an example:
 * ```python
 * lines_up_here_are_excluded()
 * # begin section
 * lines_between_the_markers_are_preserved()
 * assert pretty_neat_huh()
 * # end section
 * lines_down_here_are_excluded_too()
 * ```
 * We can select only the two lines between the comments by invoking the function as:
 * `limitSnippetLines(content, null, 0, '# begin section', '# end section');`
 *
 * @param {string} content - Whole file snippet contents
 * @param {string} fromTo - Usually in the following format: '26-28'
 * @param {int} dedent - Optional line dedent
 * @param {string} startAfter - Optional substring of a line in `content` to start after
 * @param {string} endBefore - Optional substring of a line in `content` to start after. If
 *  `startAfter` is specified, `endBefore` must occur later in content.
 * @throws {Error} Will throw an error if `fromTo` is not formatted well.
 */
export const limitSnippetLines = (content, fromTo, dedent, startAfter, endBefore) => {
  const dedentLevel = dedent ? parseInt(dedent) : 0;

  let elements = content.split(SPLIT_PATTERN);

  if (startAfter) {
    const startIndex = elements.findIndex((l) => l.includes(startAfter));
    if (startIndex === -1) {
      throw new Error(`No match for startAfter value "${startAfter}"`);
    }
    elements = elements.slice(startIndex + 1);
  }
  if (endBefore) {
    const endIndex = elements.findIndex((l) => l.includes(endBefore));
    if (endIndex === -1) {
      throw new Error(`No match for endBefore value "${endBefore}"`);
    }
    elements = elements.slice(0, endIndex);
  }

  const dedentedElements = elements.map((x) => x.substring(dedentLevel));
  const mypyStrippedElements = dedentedElements.map((x) =>
    x.includes(MYPY_IGNORE) ? x.substring(0, x.indexOf(MYPY_IGNORE)).trimEnd() : x,
  );

  let result = mypyStrippedElements;
  if (fromTo) {
    const desiredLineNumbers = parseLineNumbersToSet(fromTo, dedentedElements.length);
    result = result.filter((_, i) => desiredLineNumbers.has(i));
  }

  return result.join(JOIN_PATTERN);
};

/**
 * Parses the a string that specifies lines to include in a snippet. Returns a set of line numbers.
 * Heavily borrowed from Sphinx's syntax and parsing logic.
 * `spec` should be formatted like one of the following examples:
 * * `20` (only line 20)
 * * `20-25` (lines 20-25)
 * * `-25` (lines 1-20)
 * * `20-` (lines 20-end)
 *
 * Multiple of the above can be combined by separating with commas: `20,23-25,28-`
 *
 * https://github.com/sphinx-doc/sphinx/blob/ae7c4cc3b87d270bd9089c8c145f569df2557b29/sphinx/util/__init__.py#L438-L462
 * @param {string} spec a string list of from-to values or single line numbers
 * @param {int} total the total number of lines of content
 * @throws {Error} Will throw an error if `spec` is formatted incorrectly.
 */
const parseLineNumbersToSet = function parseLineNumbersToSet(spec, total) {
  const items = new Set();
  const parts = spec.split(',');
  try {
    for (const part of parts) {
      const begEnd = part.trim().split('-');
      if (begEnd.length === 1) {
        items.add(safeParseInt(begEnd[0]) - 1);
      } else if (begEnd.length === 2) {
        if (begEnd[0] === '' && begEnd[1] === '') {
          throw new Error();
        }
        const start = safeParseInt(begEnd[0] !== '' ? begEnd[0] : 1);
        const end = safeParseInt(begEnd[1] !== '' ? begEnd[1] : Math.max(start, total));
        if (start > end) {
          throw new Error(`Starting line number ${start} > ending line number ${end}`);
        }
        for (let i = start - 1; i < end; i++) {
          items.add(i);
        }
      } else {
        throw new Error();
      }
    }
  } catch (e) {
    let errString = `Invalid line number spec: ${spec}`;
    if (e.message) {
      errString += `\nReason: ${e.message}`;
    }
    throw new Error(errString);
  }

  return items;
};

/**
 * Parses a string to an int, throwing an error if it fails to do so.
 * @param {string} int the int candidate
 * @throws {Error} Will throw an error if the input string could not be parsed into an int.
 */
const safeParseInt = function safeParseInt(int) {
  const value = parseInt(int);
  if (isNaN(int)) {
    throw new Error(`Not an integer: ${int}`);
  }
  return value;
};
