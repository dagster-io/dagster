/**
 * Code Snippet API
 *
 * This API route allows retrieval and manipulation of code snippets from files.
 * It supports various parameters to extract specific portions of a file and format the output.
 *
 * Endpoint: /api/code-snippet
 *
 * Query Parameters:
 * - file (required): Path to the file relative to the DOCS_SNIPPET directory
 * - startafter (optional): Start extracting content after this string is found
 * - endbefore (optional): Stop extracting content when this string is found
 * - lines (optional): Specify which lines to include (e.g., "1-3" or "1,3,5-7")
 * - dedent (optional): Number of spaces to remove from the start of each line
 * - trim (optional): If "false", don't trim whitespace from start and end of the snippet
 *
 * Examples:
 * 1. Get entire file:
 *    /api/code-snippet?file=concepts/assets/asset_group_argument.py
 *
 * 2. Get specific lines after a marker:
 *    /api/code-snippet?file=concepts/assets/asset_group_argument.py&startafter=%23%20start_example&lines=4-6
 *
 * 3. Get content between markers, with formatting:
 *    /api/code-snippet?file=concepts/assets/asset_group_argument.py&startafter=%23%20start_example&endbefore=%23%20end_example&lines=4-6&dedent=4&trim=true
 *
 * Note: All string parameters should be URL-encoded when used in the query string.
 */

import fs from 'fs/promises';
import path from 'path';

import {NextApiRequest, NextApiResponse} from 'next';

// This makes sure the code snippets feature works in both development and production
const getSnippetsPath = async () => {
  const devPath = path.join(process.cwd(), '..', '..', 'examples', 'docs_snippets', 'docs_snippets');
  try {
    await fs.access(devPath);
    console.log('Using development snippets path:', devPath);
    return devPath;
  } catch (error) {
    const prodPath = path.join(process.cwd(), 'public', 'docs_snippets', 'docs_snippets');
    console.log('Using production snippets path:', prodPath);
    return prodPath;
  }
};

let DOCS_SNIPPET: string;

const initializeSnippetsPath = async () => {
  DOCS_SNIPPET = await getSnippetsPath();
};

initializeSnippetsPath();

const limitSnippetLines = (
  content: string,
  lines?: string,
  dedent?: number,
  startafter?: string,
  endbefore?: string,
): string => {
  console.log('limitSnippetLines input:', { 
    contentLength: content.length, 
    lines,
    dedent,
    startafter,
    endbefore,
  });

  let result = content;

  if (startafter) {
    console.log('Applying startafter:', startafter);
    const startIndex = result.indexOf(startafter);
    if (startIndex !== -1) {
      result = result.slice(startIndex + startafter.length);
      console.log('After startafter:', { resultLength: result.length });
    } else {
      console.log('startafter string not found');
    }
  }

  if (endbefore) {
    console.log('Applying endbefore:', endbefore);
    const endIndex = result.indexOf(endbefore);
    if (endIndex !== -1) {
      result = result.slice(0, endIndex);
      console.log('After endbefore:', { resultLength: result.length });
    } else {
      console.log('endbefore string not found');
    }
  }

  if (lines) {
    console.log('Applying lines filter:', lines);
    const lineNumbers = lines.split(',').flatMap(range => {
      const [start, end] = range.split('-').map(Number);
      return end ? Array.from({length: end - start + 1}, (_, i) => start + i) : [start];
    });
    console.log('Parsed line numbers:', lineNumbers);
    const allLines = result.split('\n');
    console.log('Total lines in content:', allLines.length);
    result = allLines.filter((_, i) => lineNumbers.includes(i + 1)).join('\n');
    console.log('After lines filter:', { resultLength: result.length, filteredLines: result.split('\n').length });
  }

  if (dedent) {
    console.log('Applying dedent:', dedent);
    const dedentRegex = new RegExp(`^\\s{${dedent}}`, 'gm');
    result = result.replace(dedentRegex, '');
    console.log('After dedent:', { resultLength: result.length });
  }

  console.log('limitSnippetLines output length:', result.length);
  return result;
};

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
if (!DOCS_SNIPPET) {
    await initializeSnippetsPath();
  }

  const { file, lines, startafter, endbefore, dedent, trim } = req.query;

  console.log('Snippets path:', DOCS_SNIPPET);
  console.log('Received query parameters:', req.query);

  if (typeof file !== 'string') {
    console.log('File parameter is missing or not a string');
    return res.status(400).json({ error: 'File parameter is required' });
  }

  const filePath = path.join(DOCS_SNIPPET, file);
  console.log('Attempting to read file:', filePath);

  try {
    const fileStats = await fs.stat(filePath);
    console.log('File stats:', fileStats);

    let content = await fs.readFile(filePath, 'utf8');
    console.log('File content length:', content.length);

    if (typeof content !== 'string') {
      throw new Error('File content is not a string');
    }

    console.log('Before limitSnippetLines:', {contentLength: content.length});
    content = limitSnippetLines(
      content,
      lines as string,
      dedent ? parseInt(dedent as string) : undefined,
      startafter as string,
      endbefore as string,
    );
    console.log('After limitSnippetLines:', {contentLength: content.length});

    // Remove pragmas
    if (content) {
      content = content.replace(/^\s*# (type|ruff|isort|noqa|pyright):.*$/gm, '');
      content = content.replace(/(.*?)(# (type|ruff|isort|noqa|pyright):.*)$/gm, '$1');
      console.log('Content after removing pragmas:', content.length);
    } else {
      console.error('Content is undefined after limitSnippetLines');
      throw new Error('Content became undefined after processing');
    }

    if (trim !== 'false' && content) {
      content = content.trim();
      console.log('Content after trimming:', content.length);
    }

    console.log('Final processed content length:', content.length);

    res.status(200).send(content);
  } catch (error) {
    console.error('Error reading or processing file:', error);
    res.status(500).json({
      error: 'Failed to read or process file',
      details: error.message,
      stack: error.stack,
    });
  }
}
