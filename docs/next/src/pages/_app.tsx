import { AppProps } from 'next/app';
import { useRouter } from 'next/router';
import { MDXProvider } from '@mdx-js/react';

import Layout from 'components/Layout';
import Code from 'components/Code';
import {
  AnchorHeadingsProvider,
  useAnchorHeadingsActions,
} from 'hooks/AnchorHeadings';

import 'styles/index.css';
import { useCallback, useEffect } from 'react';

const components = {
  pre: (props: any) => <div {...props} />,
  code: (props: any) => {
    return <Code {...props} />;
  },
};

function App({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const { clearAnchorHeadings } = useAnchorHeadingsActions();

  const onClearAnchorHeadings = useCallback(() => {
    try {
      clearAnchorHeadings();
    } catch (error) {
      console.log('Attempting to clean up not initialized context.');
    }
  }, [clearAnchorHeadings]);

  useEffect(() => {
    router.events.on('routeChangeStart', onClearAnchorHeadings);
    return () => {
      router.events.off('routeChangeStart', onClearAnchorHeadings);
    };
  }, [router]);

  return (
    <MDXProvider components={components}>
      <AnchorHeadingsProvider>
        <Layout>
          <Component {...pageProps} />
        </Layout>
      </AnchorHeadingsProvider>
    </MDXProvider>
  );
}

export default App;
