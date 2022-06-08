import React, { useState } from "react";

import MDXRenderer, {
  MDXData,
  VersionedContentLayout,
} from "../components/mdx/MDXRenderer";
import MDXComponents, {
  SearchIndexContext,
} from "../components/mdx/MDXComponents";
import FeedbackModal from "components/FeedbackModal";

import { SphinxPrefix, sphinxPrefixFromPage } from "../util/useSphinx";
import { versionFromPage } from "../util/useVersion";

import axios from "axios";
import { GetStaticProps } from "next";
import { MdxRemote } from "next-mdx-remote/types";
import { latestAllVersionedPaths } from "util/useNavigation";
import { promises as fs } from "fs";
import generateToc from "mdast-util-toc";
import matter from "gray-matter";
import mdx from "remark-mdx";
import path from "path";
import rehypePlugins from "components/mdx/rehypePlugins";
import remark from "remark";
import renderToString from "next-mdx-remote/render-to-string";
import { useRouter } from "next/router";

import { Shimmer } from "components/Shimmer";
import { getItems } from "components/mdx/SidebarNavigation";

const components: MdxRemote.Components = MDXComponents;

type HTMLData = {
  body: string;
  toc: string;
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

function HTMLRenderer({
  data,
  toggleFeedback,
}: {
  data: HTMLData;
  toggleFeedback: any;
}) {
  const { body, toc } = data;
  const markup = { __html: body };
  const tocMarkup = { __html: toc };

  return (
    <>
      <VersionedContentLayout>
        <div
          className="DocSearch-content prose dark:prose-dark max-w-none"
          dangerouslySetInnerHTML={markup}
        />
      </VersionedContentLayout>

      <aside className="hidden relative xl:block flex-none w-80 flex shrink-0 border-l border-gray-200">
        {/* Start secondary column (hidden on smaller screens) */}
        <div className="flex flex-col justify-between sticky top-24 py-6 px-4">
          <div className="mb-8 px-4 py-2 relative overflow-y-scroll max-h-(screen-60)">
            <div className="font-semibold text-gable-green">On This Page</div>
            <div className="mt-6 prose" dangerouslySetInnerHTML={tocMarkup} />
          </div>
        </div>
        {/* End secondary column */}
      </aside>
    </>
  );
}

export default function MdxPage(props: Props) {
  const [isFeedbackOpen, setOpenFeedback] = useState<boolean>(false);

  const closeFeedback = () => {
    setOpenFeedback(false);
  };

  const toggleFeedback = () => {
    setOpenFeedback(!isFeedbackOpen);
  };

  const router = useRouter();

  // If the page is not yet generated, this shimmer/skeleton will be displayed
  // initially until getStaticProps() finishes running
  if (router.isFallback) {
    return <Shimmer />;
  }

  return (
    <>
      <FeedbackModal isOpen={isFeedbackOpen} closeFeedback={closeFeedback} />
      {props.type == PageType.MDX ? (
        <MDXRenderer data={props.data} toggleFeedback={toggleFeedback} />
      ) : (
        <HTMLRenderer data={props.data} toggleFeedback={toggleFeedback} />
      )}
    </>
  );
}

async function getVersionedContent(
  version: string,
  asPath: string
): Promise<string> {
  const bucket = "dagster-docs-versioned-content";
  const region = "us-west-1";
  const folder = "versioned_content";
  const url = `https://${bucket}.s3.${region}.amazonaws.com/${folder}/${version}${asPath}`;
  const response = await axios.get(url, { transformResponse: (x) => x });
  return response.data;
}

async function getContent(version: string, asPath: string) {
  if (version == "master") {
    // render files from the local content folder
    const basePath = path.resolve("../content");
    const pathToFile = path.join(basePath, asPath);
    const buffer = await fs.readFile(pathToFile);
    const contentString = buffer.toString();
    return contentString;
  } else {
    // render versioned files from remote bucket
    const contentString = await getVersionedContent(version, asPath);
    return contentString;
  }
}

async function getSphinxData(
  sphinxPrefix: SphinxPrefix,
  version: string,
  page: string[]
) {
  if (sphinxPrefix === SphinxPrefix.API_DOCS) {
    const content = await getContent(version, "/api/sections.json");
    const {
      api: { apidocs: data },
    } = JSON.parse(content);

    let curr = data;
    for (const part of page) {
      curr = curr[part];
    }

    const { body, toc } = curr;

    return {
      props: { type: PageType.HTML, data: { body, toc } },
    };
  } else {
    const content = await getContent(version, "/api/modules.json");
    const data = JSON.parse(content);
    let curr = data;
    for (const part of page) {
      curr = curr[part];
    }

    const { body } = curr;

    return {
      props: { type: PageType.HTML, data: { body } },
    };
  }
}

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const { page } = params;
  const { version, asPath } = versionFromPage(page);

  const { sphinxPrefix, asPath: subPath } = sphinxPrefixFromPage(asPath);
  // If the subPath == "/", then we continue onto the MDX render to render the _apidocs.mdx page
  if (sphinxPrefix && subPath !== "/") {
    try {
      return getSphinxData(sphinxPrefix, version, subPath.split("/").splice(1));
    } catch (err) {
      console.log(err);
      return { notFound: true };
    }
  }

  const githubLink = new URL(
    path.join(
      "dagster-io/dagster/tree/master/docs/content",
      "/",
      asPath + ".mdx"
    ),
    "https://github.com"
  ).href;

  try {
    // 1. Read and parse versioned search
    const searchContent = await getContent(version, "/api/searchindex.json");
    const searchIndex = JSON.parse(searchContent);

    // 2. Read and parse versioned MDX content
    const source = await getContent(version, asPath + ".mdx");
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
        type: PageType.MDX,
        data: {
          mdxSource: mdxSource,
          frontMatter: data,
          searchIndex: searchIndex,
          tableOfContents,
          githubLink,
          asPath,
        },
      },
      revalidate: 600, // In seconds; This enables Incremental Static Regeneration
    };
  } catch (err) {
    console.error(err);
    return {
      notFound: true,
    };
  }
};

export function getStaticPaths({}) {
  return {
    paths: latestAllVersionedPaths(), // only generate pages of latest version at build time
    fallback: true,
  };
}
