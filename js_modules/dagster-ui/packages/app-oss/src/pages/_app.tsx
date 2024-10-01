import {AppProps} from 'next/app';
import Head from 'next/head';

// eslint-disable-next-line import/no-default-export
export default function MyApp({Component, pageProps}: AppProps) {
  return (
    <>
      <Head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
        <meta name="theme-color" content="#000000" />
        <meta name="slack-app-id" content="A036YAU6RT7" />
        <title>Dagster</title>
      </Head>
      <Component {...pageProps} />
    </>
  );
}
