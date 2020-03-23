import fg from "fast-glob";
import path from "path";
import { promises as fs } from "fs";
import parse5 from "parse5";
import { parse } from "querystring";
import algoliasearch from "algoliasearch";
import data from "../data/searchindex.json";

// Environment Variables

// Folder paths
const DATA_PATH = path.join(__dirname, "../data");
const MODULE_PATH = path.join(DATA_PATH, "_modules");

(async () => {
  /* Generate list of all module files */
  const glob = path.join(DATA_PATH, "/**/*.json");
  const excludeGlob = path.join(MODULE_PATH, "/**/*.json");
  const entries = await fg([glob], { ignore: [excludeGlob] });

  for (const entry of entries) {
    const rawData = (await fs.readFile(entry)).toString();
    const fileData = JSON.parse(rawData);
    const body: string = fileData.body;
    if (body) {
      const transformed = body
        .replace(/href="\.\.\/.*?(\/#.*?)"/g, match => {
          return match.replace("/#", "#");
        })
        .replace(/href="(\.\.\/)[^.]/g, (match, p1) => {
          return match.replace(p1, "");
        });
      fileData.body = transformed;
      await fs.writeFile(entry, JSON.stringify(fileData), "utf8");
    }
  }
})();

(async () => {
  /* Generate list of all module files */
  const glob = path.join(MODULE_PATH, "/**/*.json");
  const rootGlob = path.join(MODULE_PATH, "/*.json");
  const entries = await fg([glob]);
  const excludeEntries = await fg([rootGlob]);
  const relativeEntries = entries
    .filter(i => !excludeEntries.includes(i))
    .map(i => path.relative(MODULE_PATH, i).replace(".json", ""));

  const index = {
    docnames: relativeEntries
  };
  await fs.writeFile(
    path.join(MODULE_PATH, "searchindex.json"),
    JSON.stringify(index)
  );
})();

(async () => {
  const {
    NEXT_ALGOLIA_APP_ID,
    NEXT_ALGOLIA_API_KEY,
    NEXT_ALGOLIA_ADMIN_KEY
  } = process.env;

  if (!NEXT_ALGOLIA_APP_ID) {
    console.error("Environment variable NEXT_ALGOLIA_APP_ID not set");
    process.exit(1);
  } else if (!NEXT_ALGOLIA_ADMIN_KEY) {
    console.error("Environment variable NEXT_ALGOLIA_ADMIN_KEY not set");
    process.exit(1);
  }

  /* Setup index */
  const client = algoliasearch(NEXT_ALGOLIA_APP_ID, NEXT_ALGOLIA_ADMIN_KEY);
  const index = client.initIndex("docs");
  const records = [];

  const objects: {
    [key: string]: {
      [key: string]: (number | string)[];
    };
  } = data.objects;
  for (const module in objects) {
    for (const object in objects[module]) {
      const objProperties = objects[module][object];
      const docNamesIndex: number = objProperties[0] as number;
      const typeIndex: number = objProperties[1] as number;
      const alias: string = objProperties[3] as string;
      const objectNames: {
        [key: number]: string[];
      } = data.objnames;

      const relativePath = data.docnames[docNamesIndex].replace(
        "sections/api/apidocs/",
        ""
      );

      const path =
        alias === ""
          ? relativePath + `#${module}.${object}`
          : relativePath + "#" + alias;

      const record = {
        module,
        object,
        path,
        type: objectNames[typeIndex][1],
        alias
      };
      records.push(record);
    }
  }

  index.saveObjects(records, { autoGenerateObjectIDIfNotExist: true });
})();
