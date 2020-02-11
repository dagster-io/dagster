const path = require("path");
const fs = require("fs-extra");
const gitTags = require("remote-git-tags");

const DAGSTER_INFO_PATH = path.join(__dirname, "../../dagster-info.json");
exports.DAGSTER_INFO_PATH = DAGSTER_INFO_PATH;

exports.getCurrentVersion = () => {
  const info = fs.readJSONSync(DAGSTER_INFO_PATH);
  return info.version;
};

exports.getAllBuildedVersions = () => {
  const docsDir = path.join(__dirname, "../../versions");
  return fs
    .readdirSync(docsDir, { withFileTypes: true })
    .filter(dir => dir.isDirectory())
    .map(dir => dir.name);
};

exports.getAllVersions = async () => {
  const map = await gitTags("https://github.com/dagster-io/dagster");
  return Array.from(map.entries()).map(([vs]) => vs);
};
