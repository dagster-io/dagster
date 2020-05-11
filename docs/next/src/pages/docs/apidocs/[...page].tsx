import { NextPage } from 'next';
import { GetStaticProps } from 'next';
import { getApiDocsPaths } from 'lib/apiDocsPaths';

const API: NextPage<{ body: string }> = (props) => {
  const markup = { __html: props.body };
  return <div dangerouslySetInnerHTML={markup} />;
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

  const data = await import('../../../data/' + page.join('/') + '.json');
  return {
    props: {
      body: data.body,
    },
  };
};

export async function getStaticPaths() {
  return getApiDocsPaths();
}

export default API;
