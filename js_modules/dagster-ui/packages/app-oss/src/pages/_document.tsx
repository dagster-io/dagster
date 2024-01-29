import fs from 'fs';
import path from 'path';

import {Head, Html, Main, NextScript} from 'next/document';

function getSecurityPolicy() {
  return fs.readFileSync(path.join(__dirname, '../../../csp-header-dev.txt'), {encoding: 'utf8'});
}

// eslint-disable-next-line import/no-default-export
export default function Document() {
  const isDev = process.env.NODE_ENV === 'development';
  return (
    <Html lang="en">
      <Head nonce="NONCE-PLACEHOLDER">
        <script
          nonce="NONCE-PLACEHOLDER"
          dangerouslySetInnerHTML={{
            __html: 'window.__webpack_public_path__ = "__PATH_PREFIX__"',
          }}
        />
        {/* Not sure if we need the following script */}
        <script
          id="webpack-nonce-setter"
          nonce="NONCE-PLACEHOLDER"
          dangerouslySetInnerHTML={{__html: `__webpack_nonce__ = 'NONCE-PLACEHOLDER';`}}
        />
        {isDev ? <meta httpEquiv="Content-Security-Policy" content={getSecurityPolicy()} /> : null}
        <script
          type="application/json"
          id="initialization-data"
          nonce="NONCE-PLACEHOLDER"
          dangerouslySetInnerHTML={{
            __html: `
    {
      "pathPrefix": "__PATH_PREFIX__",
      "telemetryEnabled": "__TELEMETRY_ENABLED__",
      "liveDataPollRate": "__LIVE_DATA_POLL_RATE__"
    }
  `,
          }}
        />
        <link
          rel="manifest"
          href={`${process.env.NEXT_PUBLIC_URL ?? ''}/manifest.json`}
          crossOrigin="use-credentials"
        />
        <link
          rel="icon"
          type="image/png"
          href={`${process.env.NEXT_PUBLIC_URL ?? ''}/favicon.png`}
        />
        <link
          rel="icon"
          type="image/svg+xml"
          href={`${process.env.NEXT_PUBLIC_URL ?? ''}/favicon.svg`}
        />
      </Head>
      <body>
        <Main />
        <NextScript nonce="NONCE-PLACEHOLDER" />
      </body>
    </Html>
  );
}
