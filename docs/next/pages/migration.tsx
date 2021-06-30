import MDXComponents, {
  SearchIndexContext,
} from "../components/mdx/MDXComponents";

import { GetStaticProps } from "next";
import Link from "../components/Link";
import { MdxRemote } from "next-mdx-remote/types";
import { NextSeo } from "next-seo";
import SidebarNavigation from "components/mdx/SidebarNavigation";
import { promises as fs } from "fs";
import generateToc from "mdast-util-toc";
import hydrate from "next-mdx-remote/hydrate";
import matter from "gray-matter";
import mdx from "remark-mdx";
import path from "path";
import rehypePlugins from "components/mdx/rehypePlugins";
import remark from "remark";
import renderToString from "next-mdx-remote/render-to-string";
import { useRouter } from "next/router";
import { useVersion } from "../util/useVersion";
import visit from "unist-util-visit";

const components: MdxRemote.Components = MDXComponents;

type MDXData = {
  mdxSource: MdxRemote.Source;
  frontMatter: {
    title: string;
    description: string;
  };
  searchIndex: any;
  tableOfContents: any;
  githubLink: string;
};

type HTMLData = {
  body: string;
};

enum PageType {
  MDX = "MDX",
  HTML = "HTML",
}

type Props =
  | {
      type: PageType.MDX;
      data: MDXData;
    }
  | { type: PageType.HTML; data: HTMLData };

export const VersionNotice = () => {
  const { asPath, version, defaultVersion } = useVersion();

  if (version == defaultVersion) {
    return null;
  }

  return (
    <div className="bg-yellow-100 mb-10 mt-6 shadow sm:rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          {version === "master"
            ? "You are viewing an unreleased version of the documentation."
            : "You are viewing an outdated version of the documentation."}
        </h3>
        <div className="mt-2 text-sm text-gray-500">
          {version === "master" ? (
            <p>
              This documentation is for an unreleased version ({version}) of
              Dagster. The content here is not guaranteed to be correct or
              stable. You can view the version of this page rom our latest
              release below.
            </p>
          ) : (
            <p>
              This documentation is for an older version ({version}) of Dagster.
              A new version of this page is available for our latest
            </p>
          )}
        </div>
        <div className="mt-3 text-sm">
          <Link href={asPath} version={defaultVersion}>
            <a className="font-medium text-indigo-600 hover:text-indigo-500">
              {" "}
              View Latest Documentation <span aria-hidden="true">→</span>
            </a>
          </Link>
        </div>
      </div>
    </div>
  );
};

function MDXRenderer({ data }: { data: MDXData }) {
  const { query } = useRouter();
  const { editMode } = query;

  const {
    mdxSource,
    frontMatter,
    searchIndex,
    tableOfContents,
    githubLink,
  } = data;

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

        <VersionNotice />
        <div className="py-6 px-4 sm:px-6 lg:px-8 w-full">
          <div className="prose dark:prose-dark max-w-none">{content}</div>
        </div>
        {/* End main area */}
      </div>
      {!editMode && (
        <aside className="hidden relative xl:block flex-none w-96 flex-shrink-0 border-gray-200">
          {/* Start secondary column (hidden on smaller screens) */}
          <div className="flex flex-col justify-between  sticky top-24  py-6 px-4 sm:px-6 lg:px-8">
            <div className="mb-8 border px-4 py-4 relative overflow-y-scroll max-h-(screen-60)">
              <div className="uppercase text-sm font-semibold text-gray-500">
                On this page
              </div>
              <div className="mt-6 ">
                {tableOfContents.items[0].items && (
                  <SidebarNavigation items={tableOfContents.items[0].items} />
                )}
              </div>
            </div>

            <div className="mb-8 border px-4 py-4 relative overflow-y-scroll max-h-(screen-60)">
              <div className="flex items-center group">
                <svg
                  className="h-4 w-4 text-gray-500 group-hover:text-gray-900 transition transform group-hover:scale-105 group-hover:rotate-6"
                  role="img"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <title>GitHub icon</title>
                  <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
                </svg>
                <a
                  className="ml-2 font-semibold text-md text-gray-500 group-hover:text-gray-800"
                  href={githubLink}
                >
                  Edit Page on Github
                </a>
              </div>
            </div>
          </div>
          {/* End secondary column */}
        </aside>
      )}
    </>
  );
}

function HTMLRenderer({ data }: { data: HTMLData }) {
  const { body } = data;
  const markup = { __html: body };

  return (
    <>
      <div
        className="flex-1 min-w-0 relative z-0 focus:outline-none pt-8"
        tabIndex={0}
      >
        {/* Start main area*/}
        <div className="py-6 px-4 sm:px-6 lg:px-8 w-full">
          <div
            className="prose dark:prose-dark max-w-none"
            dangerouslySetInnerHTML={markup}
          />
        </div>
        {/* End main area */}
      </div>
    </>
  );
}

export default function MdxPage(props: Props) {
  const router = useRouter();

  // If the page is not yet generated, this will be displayed
  // initially until getStaticProps() finishes running
  if (router.isFallback) {
    return (
      <div className="w-full my-12 h-96 animate-pulse prose max-w-none">
        <div className="bg-gray-200 px-4 w-48 h-12"></div>
        <div className="bg-gray-200 mt-12 px-4 w-1/2 h-6"></div>
        <div className="bg-gray-200 mt-5 px-4 w-2/3 h-6"></div>
        <div className="bg-gray-200 mt-5 px-4 w-1/3 h-6"></div>
        <div className="bg-gray-200 mt-5 px-4 w-1/2 h-6"></div>
      </div>
    );
  }

  if (props.type == PageType.MDX) {
    return <MDXRenderer data={props.data} />;
  } else {
    return <HTMLRenderer data={props.data} />;
  }
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

export const getStaticProps: GetStaticProps = async () => {
  const githubLink = new URL(
    path.join("dagster-io/dagster/blob/master/MIGRATION.md"),
    "https://github.com"
  ).href;
  const pathToMdxFile = path.resolve("../../MIGRATION.md");

  try {
    // 2. Read and parse versioned MDX content
    const source = await fs.readFile(pathToMdxFile);
    const { content, data } = matter(source);

    // 3. Extract table of contents from MDX
    const tree = remark().use(mdx).parse(content);
    const node = generateToc(tree, { maxDepth: 4 });
    const tableOfContents = getItems(node.map, {});

    // 4. Render MDX
    const mdxSource = await renderToString(content, {
      components,
      mdxOptions: {
        rehypePlugins: rehypePlugins,
      },
      scope: data,
    });

    return {
      props: {
        type: PageType.MDX,
        data: {
          mdxSource: mdxSource,
          frontMatter: data,
          tableOfContents,
          githubLink,
        },
      },
      revalidate: 10, // In seconds
    };
  } catch (err) {
    console.error(err);
    return {
      notFound: true,
    };
  }
};
