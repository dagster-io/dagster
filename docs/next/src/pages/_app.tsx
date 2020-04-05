import { AppProps } from 'next/app';
import Layout from 'components/Layout';
import Code from 'components/Code';
import 'styles/index.css';

import { MDXProvider } from '@mdx-js/react';
const components = {
  pre: (props: any) => <div {...props} />,
  code: (props: any) => {
    // To KR: Check out the props passed here to get an idea for
    // how they are formatted
    console.log(props);
    return <Code {...props} />;
  },
};

function App({ Component, pageProps }: AppProps) {
  return (
    <MDXProvider components={components}>
      <Layout>
        <Component {...pageProps} />
      </Layout>
    </MDXProvider>
  );
}

export default App;
