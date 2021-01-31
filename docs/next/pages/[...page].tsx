import path from "path";
import { promises as fs } from "fs";
import cx from "classnames";

import renderToString from "next-mdx-remote/render-to-string";
import hydrate from "next-mdx-remote/hydrate";
import { MdxRemote } from "next-mdx-remote/types";
import MDXComponents, { SearchIndexContext } from "../components/MDXComponents";
import { NextSeo } from "next-seo";

import matter from "gray-matter";
import rehypePrism from "@mapbox/rehype-prism";
import rehypeSlug from "rehype-slug";
import rehypeLink from "rehype-autolink-headings";
import rehypeAddClasses from "rehype-add-classes";

import generateTOC from "mdast-util-toc";
import remark from "remark";
import mdx from "remark-mdx";
import visit from "unist-util-visit";
import { useEffect, useState } from "react";

const components: MdxRemote.Components = MDXComponents;

interface Props {
  mdxSource: MdxRemote.Source;
  frontMatter: {
    title: string;
    description: string;
  };
  searchIndex: any;
  tableOfContents: any;
}

const getIds = (items) => {
  return items.reduce((acc, item) => {
    if (item.url) {
      // url has a # as first character, remove it to get the raw CSS-id
      acc.push(item.url.slice(1));
    }
    if (item.items) {
      acc.push(...getIds(item.items));
    }
    return acc;
  }, []);
};

const useActiveId = (itemIds) => {
  const [activeId, setActiveId] = useState(`test`);
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        });
      },
      { rootMargin: `0% 0% -95% 0%` }
    );
    itemIds.forEach((id) => {
      observer.observe(document.getElementById(id));
    });
    return () => {
      itemIds.forEach((id) => {
        observer.unobserve(document.getElementById(id));
      });
    };
  }, [itemIds]);
  return activeId;
};

const renderItems = (items, activeId, depth) => {
  const margins = ["ml-0", "ml-4", "ml-8", "ml-12"];

  return (
    <ol>
      {items.map((item) => {
        return (
          <li key={item.url} className="mt-3">
            <a
              href={item.url}
              className={cx(margins[depth], "font-semibold text-sm", {
                "text-gray-800 underline": activeId === item.url.slice(1),
                "text-gray-500": activeId !== item.url.slice(1),
              })}
            >
              {item.title}
            </a>
            {item.items && renderItems(item.items, activeId, depth + 1)}
          </li>
        );
      })}
    </ol>
  );
};

const TableOfContents = ({ items }) => {
  const idList = getIds(items);
  const activeId = useActiveId(idList);
  return (
    <div className="border px-4 py-4">
      <div className="uppercase text-sm font-bold text-gray-800 mb-6">
        On this page
      </div>
      {renderItems(items[0].items, activeId, 0)}
    </div>
  );
};

export default function ExamplePage({
  mdxSource,
  frontMatter,
  searchIndex,
  tableOfContents,
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
    <div className="w-full flex relative">
      <div className="min-w-0 flex-auto pt-10 pr-12 pb-24 lg:pb-96 prose max-w-none">
        <h1>{frontMatter.title}</h1>
        <p>{frontMatter.description}</p>
        {content}
      </div>

      <div className="hidden xl:text-sm xl:block flex-none w-72 pl-8 mr-8">
        <div className="flex flex-col justify-between overflow-y-auto sticky  pt-10 pb-6 top-10">
          <TableOfContents items={tableOfContents.items} />
        </div>
      </div>
    </div>
    </>
  );
}

// Travel the tree to get the headings
function getItems(node, current) {
  if (!node) {
    return {};
  } else if (node.type === `paragraph`) {
    visit(node, (item) => {
      if (item.type === `link`) {
        current.url = item.url;
      }
      if (item.type === `text`) {
        current.title = item.value;
      }
    });
    return current;
  } else {
    if (node.type === `list`) {
      current.items = node.children.map((i) => getItems(i, {}));
      return current;
    } else if (node.type === `listItem`) {
      const heading = getItems(node.children[0], {});
      if (node.children.length > 1) {
        getItems(node.children[1], heading);
      }
      return heading;
    }
  }
  return {};
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

    // Generate the table of contents from the AST
    const mdast = remark().use(mdx).parse(content);
    const tableOfContents = getItems(
      generateTOC(mdast, { maxDepth: 3 }).map,
      {}
    );

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
              properties: {
                className: ["no-underline", "group"],
                style: { scrollMarginTop: "100px" },
              },
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
          [
            rehypeAddClasses,
            {
              "h1,h2,h3,h4,h5,h6": "scroll-top-margin",
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
        tableOfContents,
      },
    };
  } catch (err) {
    console.error(err);
    return {
      notFound: true,
    };
  }
}
