import "../styles/globals.css";
import "../styles/prism.css";
import Layout from "../layouts/MainLayout";
import { DefaultSeo } from "next-seo";

import type { AppProps } from "next/app";
import { Container } from "next/app";

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
    <Container>
      <DefaultSeo {...DEFAULT_SEO} />
      {getLayout(<Component {...pageProps} />)}
    </Container>
  );
}

export default MyApp;
