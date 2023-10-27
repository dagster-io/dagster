import fg from 'fast-glob';
import remark from 'remark';
import extract from 'remark-extract-frontmatter';
import frontmatter from 'remark-frontmatter';
import {read, write} from 'to-vfile';
import {parse as yaml} from 'yaml';

import codeTransformer, {CodeBlockStats} from './codeBlockTransformer';

// Main
(async () => {
  const stream = fg.stream(['./pages/**/*.md']);

  const stats: CodeBlockStats = {
    totalCodeBlocks: 0,
    updatedCodeBlocks: [],
  };
  const setCodeBlockStats = (newStats: CodeBlockStats) => {
    const {totalCodeBlocks, updatedCodeBlocks} = newStats;
    stats.totalCodeBlocks += totalCodeBlocks;
    stats.updatedCodeBlocks = stats.updatedCodeBlocks.concat(updatedCodeBlocks);
  };
  for await (const path of stream) {
    const file = await read(path);
    const contents = await remark()
      // keep frontmatter
      .use(frontmatter)
      .use(extract, {yaml})
      // fill in code blocks
      .use(codeTransformer, {setCodeBlockStats})
      .process(file);

    await write({
      path,
      contents: Buffer.from(contents.toString()),
    });
  }

  console.log(`✅ ${stats.totalCodeBlocks} code blocks parsed`);
  if (stats.updatedCodeBlocks.length) {
    console.log(`⚡️ ${stats.updatedCodeBlocks.length} updated:`);
    console.log(`\t${stats.updatedCodeBlocks.join('\n\t')}`);
  } else {
    console.log(`✨ No code blocks were updated`);
  }
})();
