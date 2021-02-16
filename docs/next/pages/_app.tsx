import "../styles/globals.css";
import "../styles/prism.css";

import type { AppProps } from "next/app";
import { DefaultSeo } from "next-seo";
import Layout from "../layouts/MainLayout";

const DEFAULT_SEO = {
  title: "Dagster Docs",
  // TODO: unset this
  // while dark launch, we mark all pages to noindex
  dangerouslySetAllPagesToNoIndex: true,
};

function MyApp({ Component, pageProps }: AppProps) {
  const getLayout =
    // @ts-ignore
    Component.getLayout || ((page) => <Layout children={page} />);

  return (
    <>
      <DefaultSeo {...DEFAULT_SEO} />
      {getLayout(<Component {...pageProps} />)}
    </>
  );
}

export default MyApp;
