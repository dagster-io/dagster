import "../styles/globals.css";
import "../styles/prism.css";
import Layout from "../layouts/MainLayout";

import type { AppProps } from "next/app";

function MyApp({ Component, pageProps }: AppProps) {
  const getLayout =
    // @ts-ignore
    Component.getLayout || ((page) => <Layout children={page} />);

  return getLayout(<Component {...pageProps} />);
}

export default MyApp;
