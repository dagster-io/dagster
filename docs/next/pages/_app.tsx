import "../styles/globals.css";
import "../styles/prism.css";

import type { AppProps } from "next/app";
import { DefaultSeo } from "next-seo";
import Layout from "../layouts/MainLayout";
import { normalizeVersionPath, useVersion } from "../util/useVersion";

const BASE_URL = "docs.dagster.io";
const DEFAULT_SEO = {
  title: "Dagster Docs",
  // TODO: unset this
  // while dark launch, we mark all pages to noindex
  dangerouslySetAllPagesToNoIndex: true,
  twitter: {
    site: "@dagsterio",
    cardType: "summary_large_image",
    images: {
      url: "/assets/shared/dagster-og-share.png",
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
        url: "/assets/shared/dagster-og-share.png",
        alt: "Dagster Docs",
      },
    ],
  },
};

function MyApp({ Component, pageProps }: AppProps) {
  const { asPath } = useVersion();
  const getLayout =
    // @ts-ignore
    Component.getLayout || ((page) => <Layout children={page} />);
  const canonicalUrl = `${BASE_URL}${asPath}`;

  return (
    <>
      <DefaultSeo canonical={canonicalUrl} {...DEFAULT_SEO} />
      {getLayout(<Component {...pageProps} />)}
    </>
  );
}

export default MyApp;
