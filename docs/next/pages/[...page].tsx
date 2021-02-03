import MDXComponents, {
  SearchIndexContext,
} from "../components/mdx/MDXComponents";

import Link from "next/link";
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
import visit from "unist-util-visit";

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

export const VersionNotice = () => {
  const {
    asPath,
    locale: version,
    defaultLocale: defaultVersion,
  } = useRouter();

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
          <Link href={asPath} locale={defaultVersion}>
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

export default function MdxPage({
  mdxSource,
  frontMatter,
  searchIndex,
  tableOfContents,
}: Props) {
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
          <div className="prose max-w-none">{content}</div>
        </div>
        {/* End main area */}
      </div>
      <aside className="hidden relative xl:block flex-none w-96 flex-shrink-0 border-gray-200">
        {/* Start secondary column (hidden on smaller screens) */}
        <div className="flex flex-col justify-between  sticky top-24  py-6 px-4 sm:px-6 lg:px-8">
          <div className="mb-8 border px-4 py-4 relative overflow-y-scroll max-h-(screen-16)">
            <div className="uppercase text-sm font-semibold text-gray-500">
              On this page
            </div>
            <div className="mt-6 ">
              <SidebarNavigation items={tableOfContents.items} />
            </div>
          </div>
        </div>
        {/* End secondary column */}
      </aside>
    </>
  );
}

const basePathForVersion = (version: string) => {
  if (version === "master") {
    return path.resolve("content");
  }

  return path.resolve(".versioned_content", version);
};

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

export async function getStaticProps({ params, locale }) {
  const { page } = params;

  const basePath = basePathForVersion(locale);
  const pathToMdxFile = path.resolve(basePath, page.join("/") + ".mdx");
  const pathToSearchindex = path.resolve(basePath, "api/searchindex.json");

  try {
    // 1. Read and parse versioned search
    const buffer = await fs.readFile(pathToSearchindex);
    const searchIndex = JSON.parse(buffer.toString());

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
      provider: {
        component: SearchIndexContext.Provider,
        props: { value: searchIndex },
      },
      mdxOptions: {
        rehypePlugins: rehypePlugins,
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
      revalidate: 10, // In seconds
    };
  } catch (err) {
    console.error(err);
    return {
      notFound: true,
    };
  }
}

export function getStaticPaths({}) {
  return {
    paths: [
      {
        params: {
          page: ["concepts", "solids-pipelines", "solids"],
          locale: "master",
        },
      },

      {
        params: {
          page: ["concepts", "solids-pipelines", "pipelines"],
          locale: "master",
        },
      },
      {
        params: {
          page: ["concepts", "io-management", "io-manager"],
          locale: "master",
        },
      },
    ],
    fallback: true,
  };
}
