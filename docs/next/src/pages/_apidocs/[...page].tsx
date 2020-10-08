import { NextPage } from 'next';
import { GetStaticProps } from 'next';
import { getApiDocsPaths } from 'lib/apiDocsPaths';
import { DynamicMetaTags } from 'components/MetaTags';

const API: NextPage<{ body: string; title: string }> = (props) => {
  const markup = { __html: props.body };
  return (
    <>
      <DynamicMetaTags
        title={`API Docs - ${props.title} | Dagster`}
        // TODO https://github.com/dagster-io/dagster/issues/2835
        // meaningful description for each API page
        description="Dagster API Documentation"
      />
      <div dangerouslySetInnerHTML={markup} />
    </>
  );
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const page = params?.page;
  if (!page) {
    return {
      props: {},
    };
  }
  if (!(page instanceof Array)) {
    return <p>Not found</p>;
  }

  const data = await import('../../data/' + page.join('/') + '.json');
  return {
    props: {
      body: data.body,
      title: data.title,
    },
  };
};

export async function getStaticPaths() {
  return getApiDocsPaths();
}

export default API;
