import fs from 'fs/promises';
import path from 'path';

// Render files from the local content folder
const ROOT = path.resolve('../content');
const SAMPLE_ORIGIN = 'https://docs.dagster.io';

/**
 * For a given input path, validate that the requested file exists within the content folder.
 * If it does, return the file buffer.
 */
export async function getRealFileBuffer(inputPath: string) {
  // Sanitize the input path.
  let filePath = new URL(inputPath, SAMPLE_ORIGIN).pathname;

  // Verify that the file exists within the content folder.
  filePath = await fs.realpath(path.join(ROOT, filePath));

  if (!filePath.startsWith(ROOT)) {
    throw new Error('File not found');
  }

  // Return the file buffer.
  return await fs.readFile(filePath);
}
