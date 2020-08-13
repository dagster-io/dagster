import React from 'react';
import Head from 'next/head';

type Props = {
  title?: string;
  description?: string;
};

export function DynamicMetaTags(props: Props) {
  const {
    title = 'Dagster — A data orchestrator for machine learning, analytics, and ETL',
    description = 'Dagster lets you define pipelines in terms of the data flow between reusable, logical components. Implement components in any tool, such as Pandas, Spark, SQL, or DBT. Test locally and run anywhere. Whether you’re an individual data practitioner or building a platform to support diverse teams, Dagster supports your entire dev and deploy cycle with a unified view of data pipelines and assets.',
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
