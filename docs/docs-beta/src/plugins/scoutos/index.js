// ScoutOS Docusaurus Plugin
//
// Injects the required HTML for the ScoutOS chat bot into all pages on Docusaurus.
//
// USAGE
//
//     Include the plugin in your `docusaurus.config.js`:
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
//
//
//

const SCOUTOS_INNER_HTML = `
  document.addEventListener('DOMContentLoaded', function() {
    var copilot = document.createElement('co-pilot');
    copilot.setAttribute('copilot_id', 'dagster');
    copilot.innerHTML = \`
      <div
        slot="fab"
        style="
          background-color: var(--prism-background-color); 
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
    \`;

    document.body.appendChild(copilot);

    var script = document.createElement('script');
    script.setAttribute('type', 'module');
    script.setAttribute('src', 'https://ui.scoutos.com/copilot.js');
    document.body.appendChild(script);
  });
`;

// https://docs.scoutos.com/docs/integrations/scout-copilot#adding-the-copilot-widget-to-your-website
const SCOUTOS_COPILOT_INNER_HTML = `
  document.addEventListener('DOMContentLoaded', function() {
    var copilot = document.createElement('scout-copilot');
    copilot.setAttribute('copilot_id', 'copilot_cm61kissp00010es61qxro4dq');
    copilot.innerHTML = \`
      <div
        slot="fab"
        style="
          padding: 12px;
          border-radius: 72px;
          background: white;
          background: var(--prism-background-color);
          box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.12),
                      0px 1px 2px rgba(0, 0, 0, 0.24);
        "
      >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="url(#iconGradient)"
            width="32"
            height="32"
            viewBox="0 0 24 24"
            stroke-width="2.0"
            stroke="currentColor"
          >
            <defs>
              <linearGradient id="iconGradient" x1="80%" x2="20%" y1="0%" y2="100%">
                <stop offset="0%" stop-color="#A7FFBF"/>
                <stop offset="100%" stop-color="#4F43DD"/>
              </linearGradient>
            </defs>
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              fill="url(#iconGradient)"
              stroke="url(#iconGradient)"
              d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
          </svg>
      </div>
    \`;

    copilot.initial_activities = [
      {
        activity_type: 'llm.chat.message',
        img_url: 'https://dagster.io/images/brand/logos/dagster-primary-mark.svg',
        role: 'assistant',
        content: 'Welcome to Dagster docs! How can I help you learn about data orchestration today?',
      },
      {
        activity_type: 'action_list',
        header: 'Popular Topics',
        items: [
          {
            action_item_type: 'suggested_query',
            img_url: 'https://dagster.io/images/brand/logos/dagster-primary-mark.svg',
            title: 'Getting Started',
            query: 'How do I get started with Dagster?',
          },
          {
            action_item_type: 'suggested_query',
            img_url: 'https://dagster.io/images/brand/logos/dagster-primary-mark.svg',
            title: 'What are Assets?',
            query: 'What are software-defined assets in Dagster?',
          },
          {
            action_item_type: 'suggested_query',
            img_url: 'https://dagster.io/images/brand/logos/dagster-primary-mark.svg',
            title: 'Dagster and dbt',
            query: 'How do I integrate Dagster with dbt?',
          },
          {
            action_item_type: 'link',
            img_url: 'https://dagster.io/images/brand/logos/dagster-primary-mark.svg',
            title: 'Join Dagster Community',
            url: 'https://dagster.io/slack',
          }
        ],
      },
    ];

    document.body.appendChild(copilot);

    var script = document.createElement('script');
    script.setAttribute('type', 'module');
    script.setAttribute('src', 'https://copilot.scoutos.com/copilot.js');
    document.body.appendChild(script);
  });
`;

module.exports = function (context, options) {
  return {
    name: 'scoutos',
    injectHtmlTags() {
      return {
        headTags: [
          {
            tagName: 'script',
            attributes: {
              type: 'text/javascript',
            },
            // NOTE: we load the HTML after the `DOMContenteLoader` event as we want to prevent this
            // from being statically embedded in the HTML. One reason for this is because the
            // custom `scout-os` element fails to build due to minification errors.
            innerHTML: SCOUTOS_COPILOT_INNER_HTML,
          },
        ],
      };
    },
  };
};
