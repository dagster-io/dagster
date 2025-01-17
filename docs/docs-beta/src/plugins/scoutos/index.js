// ScoutOS Docusaurus Plugin
//
// Injects the required HTML for the ScoutOS chat bot into all pages on Docusaurus.
//
// USAGE
//
//     Requires including the `copilot.js` script in your `docusaurus.config.js`:
//
//         scripts: [
//           {
//             src: 'https://ui.scoutos.com/copilot.js',
//             async: true,
//           },
//         ],
//
//     And inclusion in your `plugins` definition:
//
//          plugins: [
//            require.resolve('./src/plugins/scoutos'),
//          ],
//
// REFERENCE
//
//     https://docs.scoutos.com/docs/integrations/scout-copilot
//     https://docusaurus.io/docs/api/plugin-methods/lifecycle-apis#injectHtmlTags
//

const scoutos_embedded_html = `
<co-pilot copilot_id="dagster">
  <div
    slot="fab"
    style="
      background-color: #E6E6FA; /* lavender */
      padding-left: 24px;
      padding-right: 24px;
      padding-top: 4px;
      padding-bottom: 4px;
      border-radius: 24px;
      display: flex;
      flex-direction: row;
      align-items: center;
      gap: 8px;
      font-weight: 500;
      font-family: "Geist", "Inter", "Arial", sans-serif;
    "
  >
    <div style="padding-top: 4px;">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
      >
        <path
          d="M6 14H14V12H6V14ZM6 11H18V9H6V11ZM6 8H18V6H6V8ZM2 22V4C2 3.45 2.19583 2.97917 2.5875 2.5875C2.97917 2.19583 3.45 2 4 2H20C20.55 2 21.0208 2.19583 21.4125 2.5875C21.8042 2.97917 22 3.45 22 4V16C22 16.55 21.8042 17.0208 21.4125 17.4125C21.0208 17.8042 20.55 18 20 18H6L2 22ZM5.15 16H20V4H4V17.125L5.15 16Z"
          fill="currentColor"
        />
      </svg>
    </div>
    <div>Ask AI</div>
  </div>
</co-pilot>
<script type="module" src="https://ui.scoutos.com/copilot.js"></script>
`;

module.exports = function (context, options) {
  return {
    name: 'scoutos',
    injectHtmlTags() {
      return {
        headTags: [
          {
            tagName: 'div',
            innerHTML: scoutos_embedded_html,
          },
        ],
      };
    },
  };
};
