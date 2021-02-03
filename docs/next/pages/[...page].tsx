import path from "path";
import { promises as fs } from "fs";

import renderToString from "next-mdx-remote/render-to-string";
import hydrate from "next-mdx-remote/hydrate";
import { MdxRemote } from "next-mdx-remote/types";
import MDXComponents, {
  SearchIndexContext,
} from "../components/mdx/MDXComponents";
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
import SidebarNavigation from "components/mdx/SidebarNavigation";

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
      <div
        className="flex-1 min-w-0 relative z-0 focus:outline-none pt-8"
        tabIndex={0}
      >
        {/* Start main area*/}
        <div className="py-6 px-4 sm:px-6 lg:px-8 w-full">
          <div className="prose max-w-none">{content}</div>
        </div>
        {/* End main area */}
      </div>
      <aside className="hidden relative xl:block flex-none w-96 flex-shrink-0 border-gray-200">
        {/* Start secondary column (hidden on smaller screens) */}
        <div className="flex flex-col justify-between overflow-y-auto sticky top-24 max-h-(screen-16) py-6 px-4 sm:px-6 lg:px-8">
          <div className="mb-8 border px-4 py-4">
            <div className="uppercase text-sm font-semibold text-gray-500">
              On this page
            </div>
            <div className="mt-6">
              <SidebarNavigation items={tableOfContents.items} />
            </div>
          </div>
        </div>
        {/* End secondary column */}
      </aside>
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
