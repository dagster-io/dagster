import DagsterVersions from './dagsterVersions.json';
import type * as Preset from '@docusaurus/preset-classic';
import type {Config} from '@docusaurus/types';
import {themes as prismThemes} from 'prism-react-renderer';

const DagsterVersionsDropdownItems = Object.entries(DagsterVersions).splice(0, 5);

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
  clientModules: [require.resolve('./src/clientModules/disableSlashSearch.js')],
  i18n: {defaultLocale: 'en', locales: ['en']},
  plugins: [
    require.resolve('docusaurus-plugin-sass'),
    require.resolve('docusaurus-plugin-image-zoom'),
    require.resolve('./src/plugins/scoutos'),
    require.resolve('./src/plugins/segment'),
    require.resolve('./src/plugins/sidebar-scroll-into-view'),
    require.resolve('./src/plugins/llms-txt'),
    // Enable local search when not in a Vercel production instance
    process.env.VERCEL_ENV !== 'production' && [
      require.resolve('docusaurus-lunr-search'),
      {
        indexBaseUrl: true,
        maxHits: 8,
        fields: {
          title: {boost: 200},
          keywords: {boost: 75},
          content: {boost: 2},
        },
        excludeRoutes: ['/tags', '/tags/**/*', '/about/**/*', '/migration/upgrading'],
      },
    ],
  ],
  themeConfig: {
    ...(process.env.ALGOLIA_APP_ID &&
      process.env.ALGOLIA_API_KEY &&
      process.env.ALGOLIA_INDEX_NAME &&
      process.env.VERCEL_ENV === 'production' && {
        algolia: {
          appId: process.env.ALGOLIA_APP_ID,
          apiKey: process.env.ALGOLIA_API_KEY,
          indexName: process.env.ALGOLIA_INDEX_NAME,
          contextualSearch: false,
        },
      }),
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
          label: 'User guide',
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
          label: 'Deployment',
          type: 'doc',
          docId: 'deployment/index',
          position: 'left',
        },
        {
          label: 'Migration',
          type: 'doc',
          docId: 'migration/index',
          position: 'left',
        },
        {
          label: 'Integrations',
          type: 'doc',
          docId: 'integrations/libraries/index',
          position: 'left',
        },
        {
          label: 'API',
          type: 'doc',
          docId: 'api/index',
          position: 'left',
        },

        // Conditionally display version dropdown when in local and Vercel production environments.
        //
        //     https://vercel.com/docs/projects/environment-variables/system-environment-variables#VERCEL_ENV
        //
        // Otherwise display a link to the latest docs site; this will used in preview builds.
        !process.env.VERCEL_ENV || process.env.VERCEL_ENV === 'production'
          ? {
              label: 'Versions',
              type: 'docsVersionDropdown',
              position: 'right',
              dropdownItemsAfter: [
                ...DagsterVersionsDropdownItems.map(([versionName, versionUrl]) => ({
                  label: versionName,
                  href: versionUrl,
                })),
                {
                  href: 'https://legacy-docs.dagster.io',
                  label: '1.9.9 and earlier',
                },
                {
                  href: 'https://main.archive.dagster-docs.io/',
                  label: 'Upcoming release (Preview)',
                },
              ],
            }
          : {
              label: 'Latest version',
              href: 'https://docs.dagster.io',
              position: 'right',
              className: 'feedback-nav-link',
            },
        {
          to: 'https://dagster.plus/',
          label: 'Sign in',
          position: 'right',
          className: 'hide-mobile',
          style: {order: 98, margin: '0px 16px 0px 48px'},
        },
        {
          to: 'https://dagster.plus/signup',
          label: 'Try Dagster+',
          position: 'right',
          className: 'cta-button hide-mobile',
          style: {order: 99, margin: '0px 0px 2px 0px'},
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
            <a href='https://github.com/dagster-io/dagster/discussions/27332'>Feedback</a>
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
        // Releases to `docs.dagster.io` are triggered on pushes to branches prefixed with
        // `release-*`, therefore the most recent release should be labeled as the version in that
        // branch (eg. `release-1.10.5`). Ultimately we will automate this process.
        docs: {
          lastVersion: 'current',
          versions: {
            current: {
              label: 'Latest (1.11.14)',
              path: '/',
            },
          },
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
