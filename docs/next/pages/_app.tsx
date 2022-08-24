import '../styles/globals.css';
import '../styles/prism.css';

import {useVersion} from 'util/useVersion';

import {DefaultSeo} from 'next-seo';
import {AppProps} from 'next/app';
import {useRouter} from 'next/router';
import * as React from 'react';

import Layout from '../layouts/MainLayout';
import * as gtag from '../util/gtag';

const BASE_URL = 'https://docs.dagster.io';
const DEFAULT_SEO = {
  title: 'Dagster Docs',
  twitter: {
    site: '@dagsterio',
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
  const {asPath} = useVersion();

  const canonicalUrl = `${BASE_URL}${asPath}`;

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
      {router.isReady ? <DefaultSeo canonical={canonicalUrl} {...DEFAULT_SEO} /> : null}
      <Layout>
        <Component {...pageProps} />
      </Layout>
    </>
  );
};

export default MyApp;
