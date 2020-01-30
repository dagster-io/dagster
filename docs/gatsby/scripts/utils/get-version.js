const path = require("path");
const fs = require("fs-extra");

exports.getCurrentVersion = () => {
  const info = fs.readJSONSync(path.join(__dirname, "../../dagster-info.json"));
  return info.version;
};

exports.getAllVersions = () => {
  const docsDir = path.join(__dirname, "../../versions/");
  return fs
    .readdirSync(docsDir, { withFileTypes: true })
    .filter(dir => dir.isDirectory())
    .map(dir => dir.name);
};
