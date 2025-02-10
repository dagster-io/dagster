import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Dagster Docs',
  tagline: 'Dagster is a Python framework for building production-grade data platforms.',
  url: 'https://docs.dagster.io',
  favicon: 'img/favicon.ico',
  baseUrl: '/',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'throw',
  onBrokenAnchors: 'throw',
  organizationName: 'dagster',
  projectName: 'dagster',
  markdown: {
    mermaid: true,
  },
  themes: ['@docusaurus/theme-mermaid'],
  i18n: {defaultLocale: 'en', locales: ['en']},
  plugins: [
    require.resolve('docusaurus-plugin-sass'),
    require.resolve('docusaurus-plugin-image-zoom'),
    require.resolve('./src/plugins/scoutos'),
    require.resolve('./src/plugins/segment'),
  ],
  themeConfig: {
    ...(process.env.ALGOLIA_APP_ID &&
      process.env.ALGOLIA_API_KEY &&
      process.env.ALGOLIA_INDEX_NAME && {
        algolia: {
          appId: process.env.ALGOLIA_APP_ID,
          apiKey: process.env.ALGOLIA_API_KEY,
          indexName: process.env.ALGOLIA_INDEX_NAME,
          contextualSearch: false,
        },
      }),
    announcementBar: {
      id: 'announcementBar',
      content: `<div><h3>Welcome to Dagster's new and improved documentation site!</h3> You can find the legacy documentation with content for versions 1.9.9 and earlier at <a target="_blank" href="https://legacy-docs.dagster.io/">legacy-docs.dagster.io</a>.</div>`,
    },
    colorMode: {
      defaultMode: 'light',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['diff', 'json', 'bash', 'docker'],
    },
    zoom: {
      selector: '.markdown > img, .tabs-container img ',
      config: {
        // options you can specify via https://github.com/francoischalifour/medium-zoom#usage
        background: {
          light: 'rgb(255, 255, 255)',
          dark: 'rgb(50, 50, 50)',
        },
      },
    },
    tableOfContents: {
      minHeadingLevel: 2,
      maxHeadingLevel: 4,
    },
    navbar: {
      hideOnScroll: true,
      logo: {
        alt: 'Dagster Logo',
        src: 'img/dagster-docs-logo.svg',
        srcDark: 'img/dagster-docs-logo-dark.svg',
        href: '/',
      },
      items: [
        {
          label: 'Docs',
          type: 'doc',
          docId: 'intro',
          position: 'left',
        },
        {
          label: 'Examples',
          type: 'doc',
          docId: 'examples/index',
          position: 'left',
        },
        {
          label: 'Integrations',
          type: 'doc',
          docId: 'integrations/libraries/index',
          position: 'left',
        },
        {
          label: 'Dagster+',
          type: 'doc',
          docId: 'dagster-plus/index',
          position: 'left',
        },
        {
          label: 'API reference',
          type: 'doc',
          docId: 'api/index',
          position: 'left',
        },
        //{
        //  label: 'Changelog',
        //  type: 'doc',
        //  docId: 'changelog',
        //  position: 'right',
        //},
        //{
        //  label: 'Versions',
        //  type: 'docsVersionDropdown',
        //  position: 'right'
        //},
        {
           label: 'Feedback',
           href: 'https://github.com/dagster-io/dagster/discussions/27332',
           position: 'right',
           className: 'feedback-nav-link',
         },
      ],
    },
    image: 'images/og.png',
    docs: {
      sidebar: {
        autoCollapseCategories: false,
        hideable: false,
      },
    },

    footer: {
      logo: {
        alt: 'Dagster Logo',
        src: 'img/dagster_labs-primary-horizontal.svg',
        srcDark: 'img/dagster_labs-reversed-horizontal.svg',
        href: '/',
      },
      links: [
        {
          html: `
          <div class='footer__items'>
            <a href='https://www.dagster.io/terms'>Terms of Service</a>
            <a href='https://www.dagster.io/privacy/'>Privacy Policy</a>
            <a href='https://www.dagster.io/security/'>Security</a>
          </div>

          <div class='footer__items--right'>
            <a href='https://twitter.com/dagster' title="X" target="_blank" rel="noreferrer noopener"><img src="/icons/twitter.svg"/></a>
            <a href='https://www.dagster.io/slack/' title="Community Slack" target="_blank" rel="noreferrer noopener"><img src="/icons/slack.svg"/></a>
            <a href='https://github.com/dagster-io/dagster' title="GitHub" target="_blank" rel="noreferrer noopener"><img src="/icons/github.svg"/></a>
            <a href='https://www.youtube.com/channel/UCfLnv9X8jyHTe6gJ4hVBo9Q/videos' title="Youtube" target="_blank" rel="noreferrer noopener"><img src="/icons/youtube.svg"/></a>
          </div>
          `,
        },
      ],
      copyright: `Copyright ${new Date().getFullYear()} Dagster Labs`,
    },
  } satisfies Preset.ThemeConfig,

  presets: [
    [
      '@docusaurus/preset-classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
          editUrl: 'https://github.com/dagster-io/dagster/tree/master/docs',
        },
        blog: false,
        theme: {
          customCss: [
            require.resolve('./node_modules/modern-normalize/modern-normalize.css'),
            require.resolve('./src/styles/custom.scss'),
          ],
        },
        // https://docusaurus.io/docs/api/plugins/@docusaurus/plugin-sitemap#ex-config
        sitemap: {
          //lastmod: 'date',
          changefreq: 'weekly',
          priority: 0.5,
          ignorePatterns: ['/tags/**'],
          filename: 'sitemap.xml',
          createSitemapItems: async (params) => {
            const {defaultCreateSitemapItems, ...rest} = params;
            const items = await defaultCreateSitemapItems(rest);
            //return items.filter((item) => !item.url.includes('/page/'));
            return items;
          },
        },
        ...(process.env.GOOGLE_ANALYTICS_TRACKING_ID && {
          gtag: {
            trackingID: process.env.GOOGLE_ANALYTICS_TRACKING_ID,
            anonymizeIP: true,
          },
        }),
      } satisfies Preset.Options,
    ],
  ],
};

export default config;
