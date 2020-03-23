import { NextPage } from "next";
import { useRouter } from "next/router";
import { GetStaticProps } from "next";
import data from "../../data/_modules/searchindex.json";

const Modules: NextPage<{ body: string }> = props => {
  const markup = { __html: props.body };
  return <div dangerouslySetInnerHTML={markup} />;
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const page = params?.page;
  if (!page) {
    return {
      props: {}
    };
  }
  if (!(page instanceof Array)) {
    return <p>Not found</p>;
  }

  const data = await import("../../data/_modules/" + page.join("/") + ".json");
  return {
    props: {
      body: data.body
    }
  };
};

export async function getStaticPaths() {
  const names = [];
  const docnames = data.docnames;
  for (const doc of docnames) {
    names.push(doc.split("/"));
  }
  return {
    paths: names.map(i => {
      return {
        params: {
          page: i
        }
      };
    }),
    fallback: false
  };
}

export default Modules;
