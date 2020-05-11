import React from 'react';
import Head from 'next/head';

type Props = {
  title?: string;
  description?: string;
};

export function DynamicMetaTags(props: Props) {
  const {
    title = 'Dagster — A Python library for building data applications',
    description = "Dagster is a system for building modern data applications. Combining an elegant programming model and beautiful UI, Dagster allows infrastructure engineers, data engineers, and data scientists to seamlessly collaborate to process and produce the trusted, reliable data needed in today's world.",
  } = props;

  return (
    <Head>
      <title key="real-title">{title}</title>
      <meta key="title" name="title" content={title} />
      <meta key="og:title" property="og:title" content={title} />
      <meta key="twitter:title" property="twitter:title" content={title} />

      <meta key="description" name="description" content={description} />
      <meta
        key="og:description"
        property="og:description"
        content={description}
      />
      <meta
        key="twitter:description"
        property="twitter:description"
        content={description}
      />
    </Head>
  );
}
