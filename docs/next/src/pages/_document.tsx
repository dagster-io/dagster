// _document is only rendered on the server side and not on the client side
import Document, {
  Head,
  DocumentInitialProps,
  Main,
  NextScript,
  DocumentContext,
} from 'next/document';

type Props = {
  initialProps: DocumentInitialProps;
  isProduction: boolean;
};

export default class MyDocument extends Document<Props> {
  static async getInitialProps(ctx: DocumentContext) {
    // Check if in production
    const isProduction = process.env.NODE_ENV === 'production';
    const initialProps = await Document.getInitialProps(ctx);
    // Pass isProduction flag back through props
    return { ...initialProps, isProduction };
  }

  // Function will be called below to inject
  // script contents onto page
  setGoogleTags() {
    return {
      __html: `
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());

          gtag('config', 'UA-138684758-1');
        `,
    };
  }

  render() {
    const { isProduction } = this.props;
    return (
      <html>
        <link rel="stylesheet" href="https://rsms.me/inter/inter.css" />
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/docsearch.js@2.6.3/dist/cdn/docsearch.min.css"
        />
        <Head>
          {/* We only want to add the scripts if in production */}
          {isProduction && (
            <>
              <script
                async
                src="https://www.googletagmanager.com/gtag/js?id=UA-138684758-1"
              />
              <script dangerouslySetInnerHTML={this.setGoogleTags()} />
            </>
          )}
        </Head>
        <body>
          <Main />
          <script src="https://cdn.jsdelivr.net/npm/docsearch.js@2.6.3/dist/cdn/docsearch.min.js"></script>
          <NextScript />
        </body>
      </html>
    );
  }
}
