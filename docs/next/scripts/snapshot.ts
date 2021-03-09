import codeTransformer, { Stats } from "../util/codeTransformer";
import { read, write } from "to-vfile";

import extract from "remark-extract-frontmatter";
import fg from "fast-glob";
import frontmatter from "remark-frontmatter";
import mdx from "remark-mdx";
import remark from "remark";
import { parse as yaml } from "yaml";

// Main
(async () => {
  const stream = fg.stream(["../content/**/*.mdx"]);

  let stats: Stats = { totalSnapshots: 0, updatedSnapshots: [] };
  const setStats = (newStats: Stats) => {
    const { totalSnapshots, updatedSnapshots } = newStats;
    stats.totalSnapshots += totalSnapshots;
    stats.updatedSnapshots = stats.updatedSnapshots.concat(updatedSnapshots);
  };

  for await (const path of stream) {
    const file = await read(path);
    const contents = await remark()
      .use(frontmatter)
      .use(extract, { yaml: yaml })
      .use({
        // This is for compatibility with Prettier settings
        settings: {
          bullet: "-",
          emphasis: "_",
          strong: "*",
          listItemIndent: "one",
          rule: "-",
        },
      })
      .use(mdx)
      .use(codeTransformer, { setStats })
      .process(file);

    await write({
      path,
      contents: Buffer.from(contents.toString()),
    });
  }

  console.log(`✅ ${stats.totalSnapshots} snapshots parsed`);
  if (stats.updatedSnapshots.length) {
    console.log(`⚡️ ${stats.updatedSnapshots.length} updated:`);
    console.log(`\t${stats.updatedSnapshots.join("\n\t")}`);
  } else {
    console.log(`✨ No snapshots were updated`);
  }
})();
