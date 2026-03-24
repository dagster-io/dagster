module.exports = {
  process(src) {
    return {code: 'module.exports = ' + JSON.stringify(src) + ';'};
  },
};
