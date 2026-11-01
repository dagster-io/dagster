// Docusaurus preset to inject Osano script as the very first script tag.
// Placing this as a preset (listed before classic) ensures it runs
// before preset-provided plugins like Google Analytics.

module.exports = function osanoPreset(_context, _options) {
  return {
    plugins: [
      function osanoPlugin() {
        return {
          name: 'osano',
          injectHtmlTags() {
            return {
              headTags: [
                {
                  tagName: 'script',
                  attributes: {
                    src: 'https://cmp.osano.com/16CVGvUGMuXuz33ME/908ae3fc-0206-4cd2-9d54-c4932c848252/osano.js',
                  },
                },
              ],
            };
          },
        };
      },
    ],
  };
};
