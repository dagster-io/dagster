import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import Translate from '@docusaurus/Translate';
import type {Props} from '@theme/NotFound/Content';
import Heading from '@theme/Heading';

export default function NotFoundContent({className}: Props): JSX.Element {
  return (
    <main className={clsx('container margin-vert--xl', className)}>
      <div className="row">
        <div className="col col--6 col--offset-3 text--center">
          <img src="/img/dagster-cowboy.png" alt="Cowboy daggy" className="wiggle" />
          <Heading as="h1" className="hero__title">
            <Translate id="theme.NotFound.title" description="The title of the 404 page">
              Sorry, partner...
            </Translate>
          </Heading>
          <p className="hero__subtitle">
            <Translate id="theme.NotFound.p1" description="The first paragraph of the 404 page">
              We can&apos;t seem to find what you&apos;re looking for.
            </Translate>
          </p>
          <p id="theme.NotFound.p2">
            If you believe this is an error&mdash;we would appreciate it if you opened a
            <Link href="https://github.com/dagster-io/dagster/issues">GitHub issue</Link>!
          </p>
        </div>
      </div>
    </main>
  );
}
