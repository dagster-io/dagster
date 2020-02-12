const path = require("path");
const fs = require("fs-extra");
const util = require("util");
const ch = require("chalk");
const sh = require("shelljs");
const arg = require("arg");
const prompts = require("prompts");

const args = arg({
  "--version": String,
  "-v": "--version"
});

const {
  getAllVersions,
  getAllBuildedVersions,
  DAGSTER_INFO_PATH
} = require("./utils/get-version");

const DOCS_BASE_DIR = path.join(__dirname, "../versions");
const NODE_MODULES = path.join(__dirname, "../node_modules");
const SPHINX_BASE_DIR = path.join(__dirname, "../../");
const GATSBY_BASE_DIR = path.join(__dirname, "../");
const SPHINX_BUILD_DIR = path.join(__dirname, "../../_build");
const SPHINX_BUILD_JSON = path.join(SPHINX_BUILD_DIR, "json");

sh.execAsync = util.promisify(sh.exec);

async function main() {
  let version = args["--version"];
  const allVersions = await getAllVersions();

  // Check if the user has Dagster development environment installed
  if (!sh.which("pyenv")) {
    console.log(ch.red("Oops, build error!"));
    console.log(
      ch.red(
        `To build the Sphinx docs you need to have locally installed all Dagster development environment.`
      )
    );
    console.log(
      ch.cyan(
        `You can read more about how do it here: ${ch.underline(
          "https://bit.ly/2Nx3hX2"
        )}`
      )
    );
  }

  // Prompt to select a version
  if (!version) {
    const response = await prompts({
      type: "autocomplete",
      name: "version",
      message: "Which version do you want to build?",
      choices: allVersions.map(vs => ({
        title: vs
      }))
    });

    version = response.version;
  }

  // Cd into dagster, checkout version and build
  process.chdir(SPHINX_BASE_DIR);
  // For now we're commenting this out -- this actually only works with some kind of submodule setup
  // Context management (see `git checkout feat/docs` below) is also very fragile
  // I think ultimately we want a script like build-version which explicitly builds a version
  // (perhaps from a tag) but we need something else that ppl can just run in dev without any git
  // shenanigans or tags etc.
  // await sh.execAsync(`git checkout tags/${version} -b tag/${version}`);
  sh.rm("-rf", SPHINX_BUILD_DIR);
  sh.rm("-rf", NODE_MODULES);
  await sh.execAsync("make json");
  // await sh.execAsync("git checkout feat/docs");
  // await sh.execAsync(`git branch -D tag/${version}`);
  await fs.writeJSON(DAGSTER_INFO_PATH, {
    version,
    all: getAllBuildedVersions()
  });

  // Converting each .fjson file into a .json file
  sh.ls("-R", "**/*.fjson").forEach(file => {
    console.log(`copying ${file}`);
    fs.copySync(file, file.replace(".fjson", ".json"));
  });

  // Creating the build folder with the current docs version
  sh.cd("../../");
  const buildDir = path.join(DOCS_BASE_DIR, version);
  await fs.ensureDir(buildDir);
  console.log(ch.green("Build folder created successfully!"));

  // Copying all generated json files into the build dir
  sh.ls("-R", `${SPHINX_BUILD_JSON}/**/*.json`).forEach(file => {
    const filename = file.replace(SPHINX_BUILD_JSON, "");
    const newFilepath = path.join(buildDir, filename);
    fs.copySync(file, newFilepath);
    console.log(ch.cyan(`Copying ${filename}`));
  });

  // Copying images to the build dir
  const imagesPath = path.join(SPHINX_BUILD_JSON, "_images");
  const newImagesPath = path.join(buildDir, "_images");
  await fs.copy(imagesPath, newImagesPath);

  // Commit build
  sh.cd(GATSBY_BASE_DIR);
  await sh.execAsync("yarn");
  // await sh.execAsync("git add versions");
  // await sh.execAsync(`git commit -m "docs: add new docs build ${version}"`);
}

main();
