import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Dagster Docs - Beta',
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
  ],
  themeConfig: {
    // Algolia environment variables are not required during development
    algolia:
      process.env.NODE_ENV === 'development'
        ? {
            appId: 'ABC123',
            apiKey: 'ABC123',
            indexName: 'ABC123',
            contextualSearch: false,
          }
        : {
            appId: process.env.ALGOLIA_APP_ID,
            apiKey: process.env.ALGOLIA_API_KEY,
            indexName: process.env.ALGOLIA_INDEX_NAME,
            contextualSearch: false,
          },
    announcementBar: {
      id: 'announcementBar',
      content: `<div><h3>This is the preview of the new documentation site.</h3> If you have any feedback, please let us know on <a target="_blank" href="https://github.com/dagster-io/dagster/discussions/24816">GitHub</a>. The current documentation can be found at <a target="_blank" href="https://docs.dagster.io/">docs.dagster.io</a>.</div>`,
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
          label: 'Integrations',
          type: 'doc',
          docId: 'integrations/index',
          position: 'left',
        },
        {
          label: 'Dagster+',
          type: 'doc',
          docId: 'dagster-plus',
          position: 'left',
        },
        {
          label: 'API Docs',
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
        {
          label: 'Feedback',
          href: 'https://github.com/dagster-io/dagster/discussions/24816',
          position: 'right',
          className: 'feedback-nav-link',
        },
      ],
    },
    image: 'img/docusaurus-social-card.jpg',
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
      copyright: `Copyright © ${new Date().getFullYear()} Dagster Labs`,
    },
  } satisfies Preset.ThemeConfig,

  presets: [
    [
      '@docusaurus/preset-classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
          editUrl: 'https://github.com/dagster-io/dagster/tree/master/docs/docs-beta',
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
      } satisfies Preset.Options,
    ],
  ],
};

export default config;
