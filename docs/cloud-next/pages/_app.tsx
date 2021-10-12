import "../styles/globals.css";
import "../styles/prism.css";

import * as gtag from "../util/gtag";

import type { AppProps } from "next/app";
import { DefaultSeo } from "next-seo";
import Layout from "../layouts/MainLayout";
import { useEffect } from "react";
import { useRouter } from "next/router";
import { useVersion } from "../util/useVersion";

const BASE_URL = "https://docs.dagster.io";
const DEFAULT_SEO = {
  title: "Dagster Docs",
  twitter: {
    site: "@dagsterio",
    cardType: "summary_large_image",
    images: {
      url: `${BASE_URL}/assets/shared/dagster-og-share.png`,
      alt: "Dagster Docs",
    },
  },
  openGraph: {
    url: BASE_URL,
    title: "Dagster Docs",
    type: "website",
    description: "A data orchestrator for machine learning, analytics, and ETL",
    images: [
      {
        url: `${BASE_URL}/assets/shared/dagster-og-share.png`,
        alt: "Dagster Docs",
      },
    ],
  },
};

function MyApp({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const { asPath } = useVersion();

  const getLayout =
    // @ts-ignore
    Component.getLayout || ((page) => <Layout children={page} />);
  const canonicalUrl = `${BASE_URL}${asPath}`;

  useEffect(() => {
    const handleRouteChange = (url) => {
      gtag.pageview(url);
    };
    router.events.on("routeChangeComplete", handleRouteChange);
    return () => {
      router.events.off("routeChangeComplete", handleRouteChange);
    };
  }, [router.events]);

  return (
    <>
      <DefaultSeo canonical={canonicalUrl} {...DEFAULT_SEO} />
      {getLayout(<Component {...pageProps} />)}
    </>
  );
}

export default MyApp;
