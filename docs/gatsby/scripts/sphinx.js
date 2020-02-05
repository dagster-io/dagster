const path = require("path");
const fs = require("fs-extra");
const util = require("util");
const ch = require("chalk");
const sh = require("shelljs");

const { getCurrentVersion } = require("./utils/get-version");

const VERSION = getCurrentVersion();
const DOCS_BASE_DIR = path.join(__dirname, "../../");
const BUILD_DIR = path.join(DOCS_BASE_DIR, "gatsby", "versions", VERSION);

const SPHINX_BUILD_DIR = path.join(__dirname, "../../_build/");
const SPHINX_BUILD_JSON = path.join(SPHINX_BUILD_DIR, "json/");

sh.execAsync = util.promisify(sh.exec);

async function main() {
  // Rebuilding Sphinx docs
  sh.rm("-rf", SPHINX_BUILD_DIR);
  await sh.execAsync("cd " + DOCS_BASE_DIR + " && make json", {
    silent: false
  });

  // Converting each .fjson file into a .json file
  sh.ls("-R", DOCS_BASE_DIR + "**/*.fjson").forEach(file => {
    console.log(`copying ${file}`);
    fs.copySync(file, file.replace(".fjson", ".json"));
  });

  // Creating the build folder with the current docs version
  console.log(`Building docs to ${BUILD_DIR}`);
  await fs.ensureDir(BUILD_DIR);

  // Copying all generated json files into the build dir
  sh.ls("-R", `${SPHINX_BUILD_JSON}/**/*.json`).forEach(file => {
    const filename = file.replace(SPHINX_BUILD_JSON, "");
    const newFilepath = path.join(BUILD_DIR, filename);
    fs.copySync(file, newFilepath);
    console.log(ch.cyan(`Copying ${filename}`));
  });

  // Copying images to the build dir
  const imagesPath = path.join(SPHINX_BUILD_JSON, "_images");
  const newImagesPath = path.join(BUILD_DIR, "_images");
  await fs.copy(imagesPath, newImagesPath);
}

main();
