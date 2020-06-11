const SPLIT_PATTERN = /\r?\n/;
const JOIN_PATTERN = '\n';

/**
 * Use this method to apply a limit for file snippets generated
 * using the ::literalinclude directive
 * @param {string} content - Whole file snippet contents
 * @param {string} fromTo - Usually in the following format: '26-28'
 * @param {int} dedent - Optional line dedent
 */
const limitSnippetLines = (content, fromTo, dedent) => {
  if (!fromTo) return content;

  const dedentLevel = dedent ? parseInt(dedent) : 0;

  let elements = content
    .split(SPLIT_PATTERN)
    .map((x) => x.substring(dedentLevel));

  const [from, to] = fromTo ? fromTo.split('-') : [];
  const start = (from ? parseInt(from) : undefined) || 1;
  const end = to ? to - start + 1 : elements.length;
  const result = elements.splice(start - 1, end);
  return result.join(JOIN_PATTERN);
};

module.exports = limitSnippetLines;
