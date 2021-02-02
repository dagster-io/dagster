import path from "path";
import { promises as fs } from "fs";

import renderToString from "next-mdx-remote/render-to-string";
import hydrate from "next-mdx-remote/hydrate";
import { MdxRemote } from "next-mdx-remote/types";
import MDXComponents, { SearchIndexContext } from "../components/MDXComponents";
import { NextSeo } from "next-seo";

import matter from "gray-matter";
import rehypePrism from "@mapbox/rehype-prism";
import rehypeSlug from "rehype-slug";
import rehypeLink from "rehype-autolink-headings";

const components: MdxRemote.Components = MDXComponents;

interface Props {
  mdxSource: MdxRemote.Source;
  frontMatter: {
    title: string;
    description: string;
  };
  searchIndex: any;
}

export default function ExamplePage({
  mdxSource,
  frontMatter,
  searchIndex,
}: Props) {
  const content = hydrate(mdxSource, {
    components,
    provider: {
      component: SearchIndexContext.Provider,
      props: { value: searchIndex },
    },
  });
  return (
    <>
      <NextSeo
        title={frontMatter.title}
        description={frontMatter.description}
      />
      <div className="prose max-w-none">
        <h1>{frontMatter.title}</h1>
        <p>{frontMatter.description}</p>
        {content}
      </div>
    </>
  );
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
  const pathToMdxFile = path.resolve(basePath, page.join("/") + ".mdx");
  try {
    // versioned searchindex
    const pathToSearchindex = path.resolve(basePath, "api/searchindex.json");
    const buffer = await fs.readFile(pathToSearchindex);
    const searchIndex = JSON.parse(buffer.toString());

    // versioned mdx
    const source = await fs.readFile(pathToMdxFile);
    const { content, data } = matter(source);

    const mdxSource = await renderToString(content, {
      components,
      provider: {
        component: SearchIndexContext.Provider,
        props: { value: searchIndex },
      },
      mdxOptions: {
        rehypePlugins: [
          rehypePrism,
          rehypeSlug,
          [
            rehypeLink,
            {
              behavior: "append",
              properties: { className: ["no-underline", "group"] },
              content: {
                type: "element",
                tagName: "span",
                properties: {
                  className: [
                    "ml-2",
                    "text-gray-200",
                    "hover:text-gray-800",
                    "hover:underline",
                  ],
                },
                children: [{ type: "text", value: "#" }],
              },
            },
          ],
        ],
      },
      scope: data,
    });
    return {
      props: {
        mdxSource: mdxSource,
        frontMatter: data,
        searchIndex: searchIndex,
      },
    };
  } catch (err) {
    console.error(err);
    return {
      notFound: true,
    };
  }
}
