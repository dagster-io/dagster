import { AppProps } from 'next/app';
import { MDXProvider, MDXProviderComponentsProp } from '@mdx-js/react';

import Layout from 'components/Layout';
import Code from 'components/Code';
import { AnchorHeadingsProvider } from 'hooks/AnchorHeadings';
import { VersionedImage } from 'components/VersionedComponents';

import 'styles/index.css';
import AnchorHeading from 'components/AnchorHeading';
import useAnchorHeadingsCleanup from 'hooks/AnchorHeadings/useAnchorHeadingsCleanup';
import useScrollToTopAfterRender from 'hooks/useScrollToTopAfterRender';
import Head from 'next/head';

const components: MDXProviderComponentsProp = {
  h2: (props) => <AnchorHeading tag={'h2'} {...props} />,
  h3: (props) => <AnchorHeading tag={'h3'} {...props} />,
  h4: (props) => <AnchorHeading tag={'h4'} {...props} />,
  h5: (props) => <AnchorHeading tag={'h5'} {...props} />,
  h6: (props) => <AnchorHeading tag={'h6'} {...props} />,
  img: (props) => <VersionedImage {...props} />,
  pre: (props: any) => <div {...props} />,
  code: (props: any) => <Code {...props} />,
};

function App({ Component, pageProps }: AppProps) {
  useAnchorHeadingsCleanup();
  useScrollToTopAfterRender();
  return (
    <>
      <Head>
        <link rel="stylesheet" href="https://rsms.me/inter/inter.css" />
      </Head>

      <MDXProvider components={components}>
        <AnchorHeadingsProvider>
          <Layout>
            <Component {...pageProps} />
          </Layout>
        </AnchorHeadingsProvider>
      </MDXProvider>
    </>
  );
}

export default App;
