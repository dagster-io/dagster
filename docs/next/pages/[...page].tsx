import renderToString from "next-mdx-remote/render-to-string";
import hydrate from "next-mdx-remote/hydrate";
import { MdxRemote } from "next-mdx-remote/types";
import path from "path";
import { promises as fs } from "fs";
import matter from "gray-matter";
import MDXComponents from "../components/MDXComponents";
import codeTransformer from "util/codeTransformer";
import rehypePrism from "@mapbox/rehype-prism";

const components: MdxRemote.Components = MDXComponents;

interface Props {
  mdxSource: MdxRemote.Source;
  frontMatter: {
    title: string;
    description: string;
  };
}

export default function ExamplePage({ mdxSource, frontMatter }: Props) {
  const content = hydrate(mdxSource, { components });
  return <div className="prose max-w-none">{content}</div>;
}

const basePathForVersion = (version: string) => {
  if (version === "master") {
    return path.resolve("content");
  }

  return path.resolve(".versioned_content", version);
};

export async function getServerSideProps({ params, locale }) {
  const { page } = params;

  const basePath = basePathForVersion(locale);
  const pathToFile = path.resolve(basePath, page.join("/") + ".mdx");

  try {
    const source = await fs.readFile(pathToFile);
    const { content, data } = matter(source);

    const mdxSource = await renderToString(content, {
      components,
      mdxOptions: {
        rehypePlugins: [rehypePrism],
      },
      scope: data,
    });

    return {
      props: {
        mdxSource: mdxSource,
        frontMatter: data,
      },
    };
  } catch (err) {
    console.error(err);
    return {
      notFound: true,
    };
  }
}
