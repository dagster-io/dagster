import { AppProps } from 'next/app';
import { useRouter } from 'next/router';
import { MDXProvider, MDXProviderComponentsProp } from '@mdx-js/react';

import Layout from 'components/Layout';
import Code from 'components/Code';
import {
  AnchorHeadingsProvider,
  useAnchorHeadingsActions,
} from 'hooks/AnchorHeadings';

import 'styles/index.css';
import { useCallback, useEffect } from 'react';
import AnchorHeading from 'components/AnchorHeading';

const components: MDXProviderComponentsProp = {
  h2: (props) => <AnchorHeading tag={'h2'} {...props} />,
  h3: (props) => <AnchorHeading tag={'h3'} {...props} />,
  h4: (props) => <AnchorHeading tag={'h4'} {...props} />,
  h5: (props) => <AnchorHeading tag={'h5'} {...props} />,
  h6: (props) => <AnchorHeading tag={'h6'} {...props} />,
  pre: (props: any) => <div {...props} />,
  code: (props: any) => <Code {...props} />,
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
