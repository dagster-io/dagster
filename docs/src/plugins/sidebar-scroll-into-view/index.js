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
    const sidebarElement = document.querySelector('aside .menu__link--active');
      if (sidebarElement) {
        observer.disconnect();
        sidebarElement.scrollIntoView({
          block: 'center',
          inline: 'nearest',
          scrollMode: 'if-needed',
          behavior: 'smooth'
        });
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  document.addEventListener("DOMContentLoaded", function() {
    handleScrollIntoView();
  });
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
