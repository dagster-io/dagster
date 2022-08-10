import fg from 'fast-glob';
import remark from 'remark';
import extract from 'remark-extract-frontmatter';
import frontmatter from 'remark-frontmatter';
import mdx from 'remark-mdx';
import {read, write} from 'to-vfile';
import {parse as yaml} from 'yaml';

import preset from '../.remarkrc.js';
import codeTransformer, {SnapshotStats} from '../util/codeTransformer';
import imageTransformer, {ImageStats} from '../util/imageTransformer';

// Main
(async () => {
  const stream = fg.stream(['../content/**/*.mdx']);

  const stats: SnapshotStats & ImageStats = {
    totalSnapshots: 0,
    updatedSnapshots: [],
    totalImages: 0,
    updatedImages: [],
  };
  const setSnapshotStats = (newStats: SnapshotStats) => {
    const {totalSnapshots, updatedSnapshots} = newStats;
    stats.totalSnapshots += totalSnapshots;
    stats.updatedSnapshots = stats.updatedSnapshots.concat(updatedSnapshots);
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
      .use(codeTransformer, {setSnapshotStats})
      .use(imageTransformer, {setImageStats})
      .use(preset)
      .process(file);

    await write({
      path,
      contents: Buffer.from(contents.toString()),
    });
  }

  console.log(`✅ ${stats.totalSnapshots} snapshots parsed`);
  if (stats.updatedSnapshots.length) {
    console.log(`⚡️ ${stats.updatedSnapshots.length} updated:`);
    console.log(`\t${stats.updatedSnapshots.join('\n\t')}`);
  } else {
    console.log(`✨ No snapshots were updated`);
  }

  console.log(`✅ ${stats.totalImages} images parsed`);
  if (stats.updatedImages.length) {
    console.log(`⚡️ ${stats.updatedImages.length} updated:`);
    console.log(`\t${stats.updatedImages.join('\n\t')}`);
  } else {
    console.log(`✨ No images were updated`);
  }
})();
