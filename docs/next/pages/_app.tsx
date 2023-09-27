import '/styles/fonts.css';
import '/styles/globals.css';
import '/styles/prism.css';
import {usePath} from 'util/usePath';

import {PersistentTabProvider} from 'components/PersistentTabContext';
import {DefaultSeo} from 'next-seo';
import {AppProps} from 'next/app';
import {useRouter} from 'next/router';
import Script from 'next/script';
import * as React from 'react';

import Layout from '../layouts/MainLayout';
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
        <Layout>
          <Component {...pageProps} />
        </Layout>
      </PersistentTabProvider>
    </>
  );
};

export default MyApp;
