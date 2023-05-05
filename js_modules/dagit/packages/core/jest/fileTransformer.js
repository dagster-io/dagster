// fileTransformer.js
const path = require('path');

module.exports = {
  process(_src, filename, _config, _options) {
    return {code: 'module.exports = ' + JSON.stringify(path.basename(filename)) + ';'};
  },
};
