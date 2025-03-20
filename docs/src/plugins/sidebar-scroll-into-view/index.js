// Fixes an issue where the sidebar is not scrolled into view on navigation.
//
//     https://github.com/facebook/docusaurus/issues/823
//
// USAGE
//
//     Include the plugin in your `docusaurus.config.js`:
//
//          plugins: [
//            require.resolve('./src/plugins/sidebar-scroll-into-view'),
//          ],
//

const INNER_HTML = `
  function handleScrollIntoView() {
    const observer = new MutationObserver(() => {
    const element = document.querySelector('aside .menu__link--active');
      if (element) {
        observer.disconnect();
        element.scrollIntoView();
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  document.addEventListener("DOMContentLoaded", function() {
    handleScrollIntoView();
  });

  const originalPushState = history.pushState;
  history.pushState = function (...args) {
    originalPushState.apply(this, args);
    window.dispatchEvent(new Event('pushstate'));  // Dispatch an event for programmatic push state
  };

  window.addEventListener('popstate', () => handleScrollIntoView());
  window.addEventListener('pushstate', () => handleScrollIntoView());
`;

module.exports = function (context, options) {
  return {
    name: 'sidebar-scroll-into-view',
    injectHtmlTags() {
      return {
        headTags: [
          {
            tagName: 'script',
            attributes: {
              type: 'text/javascript',
            },
            innerHTML: INNER_HTML,
          },
        ],
      };
    },
  };
};
