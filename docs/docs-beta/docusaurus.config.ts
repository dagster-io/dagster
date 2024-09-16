import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Dagster Docs - Beta',
  tagline: 'Dagster is a Python framework for building production-grade data platforms.',
  url: 'https://docs.dagster.io',
  favicon: 'img/favicon.ico',
  noIndex: true, // TODO - remove when production-ready

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
          docId: 'integrations',
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
        {
          label: 'Changelog',
          type: 'doc',
          docId: 'changelog',
          position: 'right',
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
          editUrl: 'https://github.com/dagster-io/dagster/tree/docs/revamp/docs/docs-beta',
        },
        blog: false,
        theme: {
          customCss: [
            require.resolve('./node_modules/modern-normalize/modern-normalize.css'),
            require.resolve('./src/styles/custom.scss'),
          ],
        },
      } satisfies Preset.Options,
    ],
  ],
};

export default config;
