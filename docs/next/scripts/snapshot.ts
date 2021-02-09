import { read, write } from "to-vfile";

import codeTransformer from "../util/codeTransformer";
import extract from "remark-extract-frontmatter";
import fg from "fast-glob";
import frontmatter from "remark-frontmatter";
import mdx from "remark-mdx";
import remark from "remark";
import { parse as yaml } from "yaml";

// Main
(async () => {
  const stream = fg.stream(["./content/**/*.mdx"]);
  for await (const path of stream) {
    console.log("Updating file", path);

    const file = await read(path);
    const contents = await remark()
      .use(frontmatter)
      .use(extract, { yaml: yaml })
      .use({
        // This is for compatability with Prettier settings
        settings: {
          bullet: "-",
          emphasis: "_",
          strong: "*",
          listItemIndent: "one",
          rule: "-",
        },
      })
      .use(mdx)
      .use(codeTransformer)
      .process(file);

    await write({
      path,
      contents: Buffer.from(contents.toString()),
    });
  }
})();
