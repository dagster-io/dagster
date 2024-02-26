import '/styles/fonts.css';
import '/styles/globals.css';
import '/styles/prism.css';
import path from 'path';
import {usePath} from 'util/usePath';

import {PersistentTabProvider} from 'components/PersistentTabContext';
import {collectHeadings, RightSidebar} from 'components/SidebarNavigation';
import {DefaultSeo} from 'next-seo';
import {AppProps} from 'next/app';
import {useRouter} from 'next/router';
import Script from 'next/script';
import * as React from 'react';

import FeedbackModal from '../components/FeedbackModal';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import {VersionedContentLayout} from '../components/mdx/MDXRenderer';
import * as gtag from '../util/gtag';

const GTM_TRACKING_ID = process.env.NEXT_PUBLIC_DOCS_GTM_ID;

const BASE_URL = 'https://docs.dagster.io';
const DEFAULT_SEO = {
  title: 'Dagster Docs',
  twitter: {
    site: '@dagster',
    cardType: 'summary_large_image',
    images: {
      url: `${BASE_URL}/assets/shared/dagster-og-share.png`,
      alt: 'Dagster Docs',
    },
  },
  openGraph: {
    url: BASE_URL,
    title: 'Dagster Docs',
    type: 'website',
    description: 'The data orchestration platform built for productivity.',
    images: [
      {
        url: `${BASE_URL}/assets/shared/dagster-og-share.png`,
        alt: 'Dagster Docs',
      },
    ],
  },
};

interface Props {
  children: React.ReactNode;
  asPath: string;
  pageProps: any;
}
const Layout = ({asPath, children, pageProps}: Props) => {
  const [isMobileDocsMenuOpen, setMobileDocsMenuOpen] = React.useState<boolean>(false);
  const openMobileDocsMenu = () => {
    setMobileDocsMenuOpen(true);
  };
  const closeMobileDocsMenu = () => {
    setMobileDocsMenuOpen(false);
  };

  const [isFeedbackOpen, setOpenFeedback] = React.useState<boolean>(false);

  const closeFeedback = () => {
    setOpenFeedback(false);
  };

  const toggleFeedback = () => {
    setOpenFeedback(!isFeedbackOpen);
  };

  const githubLink = new URL(
    path.join('dagster-io/dagster/tree/master/docs/content', '/', asPath + '.mdx'),
    'https://github.com',
  ).href;

  const {markdoc} = pageProps;
  let navigationItems = [];
  let markdownHeadings = [];
  if (markdoc) {
    markdownHeadings = markdoc?.content ? collectHeadings(markdoc.content, []) : [];
    navigationItems = [];
  } else {
    const tableOfContents = pageProps?.data?.tableOfContents;
    if (tableOfContents?.items) {
      navigationItems = tableOfContents.items.filter((item) => item?.items);
    }
  }

  // handle API docs pages (they are HTML pages generated from Sphinx, not Markdown pages)
  const isHTMLPage = pageProps?.type === 'HTML';

  return (
    <>
      <div
        style={{
          minHeight: '100vh',
          backgroundImage: 'url("/_next/image?url=/assets/head-texture.jpg&w=3840&q=100")',
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'top middle',
          backgroundSize: 'fit',
          backgroundColor: '#FAF9F7',
        }}
      >
        <Header openMobileDocsMenu={openMobileDocsMenu} />
        <div className="w-screen mx-auto px-4 sm:px-6 lg:px-8" style={{paddingTop: '48px'}}>
          <div className="mt-8 flex justify-center">
            <Sidebar
              isMobileDocsMenuOpen={isMobileDocsMenuOpen}
              closeMobileDocsMenu={closeMobileDocsMenu}
            />
            <FeedbackModal isOpen={isFeedbackOpen} closeFeedback={closeFeedback} />
            <div className="lg:pl-80 flex w-full">
              {isHTMLPage ? (
                children
              ) : (
                <>
                  <VersionedContentLayout asPath={asPath}>
                    <div className="DocSearch-content prose dark:prose-dark max-w-none">
                      {children}
                    </div>
                  </VersionedContentLayout>
                  <RightSidebar
                    markdownHeadings={markdownHeadings}
                    navigationItemsForMDX={navigationItems}
                    githubLink={githubLink}
                    toggleFeedback={toggleFeedback}
                  />
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

const MyApp = ({Component, pageProps}: AppProps) => {
  const router = useRouter();
  const asPathFromPageProps = pageProps?.data?.asPath;

  const {asPath} = usePath();

  const canonicalUrl = `${BASE_URL}${asPathFromPageProps ?? asPath}`;

  React.useEffect(() => {
    const handleRouteChange = (url: string) => {
      gtag.pageview(url);
    };
    router.events.on('routeChangeComplete', handleRouteChange);
    return () => {
      router.events.off('routeChangeComplete', handleRouteChange);
    };
  }, [router.events]);

  return (
    <>
      <DefaultSeo canonical={canonicalUrl} {...DEFAULT_SEO} />
      {/* {process.env.NODE_ENV === 'production' ? ( */}
      <>
        <Script id="gtm">
          {`(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
          new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
          j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
          'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
          })(window,document,'script','dataLayer','${GTM_TRACKING_ID}');`}
        </Script>
        <noscript>
          <iframe
            src={`https://www.googletagmanager.com/ns.html?id=${GTM_TRACKING_ID}`}
            height="0"
            width="0"
            style={{display: 'none', visibility: 'hidden'}}
          ></iframe>
        </noscript>
      </>
      {/* ) : null} */}
      <PersistentTabProvider>
        <Layout asPath={asPath} pageProps={pageProps}>
          <Component {...pageProps} />
        </Layout>
      </PersistentTabProvider>
    </>
  );
};

export default MyApp;
