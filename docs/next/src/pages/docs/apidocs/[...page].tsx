import { NextPage } from 'next';
import { GetStaticProps } from 'next';
import data from 'data/searchindex.json';

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
  const names = [];
  const docnames = data.docnames;
  for (const doc of docnames) {
    if (
      doc.includes('sections/api/') &&
      doc !== 'sections/api/index' &&
      doc !== 'sections/api/libraries'
    ) {
      names.push(doc.replace('sections/api/apidocs/', '').split('/'));
    }
  }
  return {
    paths: names.map((i) => {
      return {
        params: {
          page: i,
        },
      };
    }),
    fallback: false,
  };
}

export default API;
