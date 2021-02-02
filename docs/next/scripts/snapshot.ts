import { read, write } from "to-vfile";
import remark from "remark";
import mdx from "remark-mdx";
import codeTransformer from "../util/codeTransformer";

// This is to keep front matter in place
import frontmatter from "remark-frontmatter";
import extract from "remark-extract-frontmatter";
import { parse as yaml } from "yaml";

// Main
(async () => {
  const path = "./content/concepts/solids-pipelines/solids.mdx";
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
})();
