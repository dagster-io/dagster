import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import type {Props} from '@theme/NotFound/Content';
import Heading from '@theme/Heading';

export default function NotFoundContent({className}: Props): JSX.Element {
  return (
    <main className={clsx('margin-vert--xl', className)}>
      <div className="row">
        <div className="col col--6 col--offset-3">
          <div className="text--center">
            <Heading as="h1" className="not-found-title hover-wiggle">
              404
            </Heading>
            <p className="hero__subtitle">
              We can&apos;t seem to find what you&apos;re looking for.
            </p>
            <p id="theme.NotFound.p2">
              If you believe that this is an error&mdash;we would greatly appreciate it if you
              opened a <Link href="https://github.com/dagster-io/dagster/issues">GitHub issue</Link>
              .
            </p>
          </div>
          <div className="not-found-links card">
            <Link href="/">Welcome to Dagster</Link>
            <Link href="/getting-started/quickstart">Build your first Dagster project</Link>
            <Link href="/tutorial/tutorial-etl">Build your first ETL pipeline</Link>
          </div>
        </div>
      </div>
    </main>
  );
}
