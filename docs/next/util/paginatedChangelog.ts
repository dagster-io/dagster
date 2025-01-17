import {promises as fs} from 'fs';
import path from 'path';

import matter from 'gray-matter';

type Result = {
  pageContentList: Array<string>;
  frontMatterData: {[key: string]: any};
};

const cache: Map<
  number, // `versionCountPerPage`. It won't really change in production but might be updated during development
  Result | null
> = new Map();

export async function getPaginatedChangeLog(input: {versionCountPerPage: number}): Promise<Result> {
  const {versionCountPerPage} = input;

  const maybeCached = cache.get(versionCountPerPage);
  if (maybeCached != null) {
    return maybeCached;
  }

  const result = await getPaginatedChangeLogImpl({
    versionCountPerPage,
  });

  cache.set(versionCountPerPage, result);
  return result;
}

async function getPaginatedChangeLogImpl(input: {versionCountPerPage: number}): Promise<Result> {
  const {versionCountPerPage} = input;

  const pathToMdxFile = path.resolve(process.cwd(), '../../CHANGES.md');
  const source = await fs.readFile(pathToMdxFile);
  const {content: fullContent, data: frontMatterData} = matter(source);

  const lineList = fullContent.split('\n');

  // Mark the line indices of all version notes
  const versionMarkerList = [];
  for (let i = 0; i < lineList.length; i++) {
    const line = lineList[i];
    if (/^## \d/.test(line)) {
      versionMarkerList.push(i);
    }
  }

  // Everything above the first version note ("# Changelog")
  const sharedHeader = lineList.slice(0, versionMarkerList[0]).join('\n');

  const versionNoteList = versionMarkerList.map((marker, index) => {
    const endIndex =
      index === versionMarkerList.length - 1 ? undefined : versionMarkerList[index + 1];

    return lineList.slice(marker, endIndex).join('\n');
  });

  const pageContentList: Array<string> = [];
  let window: Array<string> = [];

  for (let i = 0; i < versionNoteList.length; i++) {
    if (window.length >= versionCountPerPage) {
      window.unshift(sharedHeader);
      pageContentList.push(window.join('\n'));
      window = [];
    }

    window.push(versionNoteList[i]);
  }

  if (window.length > 0) {
    window.unshift(sharedHeader);
    pageContentList.push(window.join('\n'));
  }

  return {pageContentList, frontMatterData};
}
