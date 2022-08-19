import fg from 'fast-glob';
import remark from 'remark';
import extract from 'remark-extract-frontmatter';
import frontmatter from 'remark-frontmatter';
import mdx from 'remark-mdx';
import {read, write} from 'to-vfile';
import {parse as yaml} from 'yaml';
import preset from "../.remarkrc.js";
import codeTransformer, { CodeBlockStats } from "../util/codeBlockTransformer";
import imageTransformer, { ImageStats } from "../util/imageTransformer";

// Main
(async () => {
  const stream = fg.stream(['../content/**/*.mdx']);

  let stats: CodeBlockStats & ImageStats = {
    totalCodeBlocks: 0,
    updatedCodeBlocks: [],
    totalImages: 0,
    updatedImages: [],
  };
  const setCodeBlockStats = (newStats: CodeBlockStats) => {
    const { totalCodeBlocks, updatedCodeBlocks } = newStats;
    stats.totalCodeBlocks += totalCodeBlocks;
    stats.updatedCodeBlocks = stats.updatedCodeBlocks.concat(updatedCodeBlocks);
  };
  const setImageStats = (newStats: ImageStats) => {
    const {totalImages, updatedImages} = newStats;
    stats.totalImages += totalImages;
    stats.updatedImages = stats.updatedImages.concat(updatedImages);
  };
  for await (const path of stream) {
    const file = await read(path);
    const contents = await remark()
      .use(frontmatter)
      .use(extract, {yaml})
      .use(mdx)
      .use(codeTransformer, { setCodeBlockStats })
      .use(imageTransformer, { setImageStats })
      .use(preset)
      .process(file);

    await write({
      path,
      contents: Buffer.from(contents.toString()),
    });
  }

  console.log(`✅ ${stats.totalCodeBlocks} code blocks parsed`);
  if (stats.updatedCodeBlocks.length) {
    console.log(`⚡️ ${stats.updatedCodeBlocks.length} updated:`);
    console.log(`\t${stats.updatedCodeBlocks.join("\n\t")}`);
  } else {
    console.log(`✨ No code blocks were updated`);
  }

  console.log(`✅ ${stats.totalImages} images parsed`);
  if (stats.updatedImages.length) {
    console.log(`⚡️ ${stats.updatedImages.length} updated:`);
    console.log(`\t${stats.updatedImages.join('\n\t')}`);
  } else {
    console.log(`✨ No images were updated`);
  }
})();
