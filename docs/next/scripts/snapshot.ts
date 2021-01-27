import { read, write } from "to-vfile";
import remark from "remark";
import mdx from "remark-mdx";
import codeTransformer from "../util/codeTransformer";

// Main
(async () => {
  const path = "./content/concepts/solids-pipelines/solids.mdx";
  const file = await read(path);
  const contents = await remark()
    .use({
      // This is for compatability with Prettier settings
      settings: { bullet: "-", emphasis: "_", strong: "_" },
    })
    .use(mdx)
    .use(codeTransformer)
    .process(file);

  console.log(contents.toString());

  await write({
    path,
    contents: Buffer.from(contents.toString()),
  });
})();
