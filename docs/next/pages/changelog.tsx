import path from 'path';

import {Shimmer} from 'components/Shimmer';
import rehypePlugins from 'components/mdx/rehypePlugins';
import generateToc from 'mdast-util-toc';
import {GetServerSideProps} from 'next';
import renderToString from 'next-mdx-remote/render-to-string';
import {MdxRemote} from 'next-mdx-remote/types';
import {useRouter} from 'next/router';
import React from 'react';
import remark from 'remark';
import mdx from 'remark-mdx';
import visit from 'unist-util-visit';

import FeedbackModal from '../components/FeedbackModal';
import {PagePagination} from '../components/PagePagination';
import MDXComponents from '../components/mdx/MDXComponents';
import MDXRenderer, {MDXData} from '../components/mdx/MDXRenderer';
import {getPaginatedChangeLog} from '../util/paginatedChangelog';

const PAGINATION_VERSION_COUNT_PER_PAGE = 5;
const PAGINATION_QUERY_NAME = 'page';

// The next-mdx-remote types are outdated.
const components: MdxRemote.Components = MDXComponents as any;

enum PageType {
  MDX = 'MDX',
}

type Props = {
  type: PageType.MDX;
  data: MDXData;
  totalPageCount: number;
};

export default function MdxPage(props: Props) {
  const [isFeedbackOpen, setOpenFeedback] = React.useState<boolean>(false);

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

  const currentPageIndex = getPageIndexFromQuery(
    router.query[PAGINATION_QUERY_NAME],
    props.totalPageCount,
  );

  return (
    <>
      <MDXRenderer data={props.data} />
      <PagePagination currentPageIndex={currentPageIndex} totalPageCount={props.totalPageCount} />
    </>
  );
}

// Travel the tree to get the headings
function getMDXItems(node, current) {
  if (!node) {
    return {};
  } else if (node.type === `paragraph`) {
    visit(node, (item) => {
      if (item.type === `link`) {
        current.url = item['url'];
      }
      if (item.type === `text`) {
        current.title = item['value'];
      }
    });
    return current;
  } else {
    if (node.type === `list`) {
      current.items = node.children.map((i) => getMDXItems(i, {}));
      return current;
    } else if (node.type === `listItem`) {
      const heading = getMDXItems(node.children[0], {});
      if (node.children.length > 1) {
        getMDXItems(node.children[1], heading);
      }
      return heading;
    }
  }
  return {};
}

export const getServerSideProps: GetServerSideProps = async (context) => {
  const githubLink = new URL(
    path.join('dagster-io/dagster/blob/master/CHANGES.md'),
    'https://github.com',
  ).href;

  try {
    // 2. Read and parse versioned MDX content
    const {pageContentList, frontMatterData: data} = await getPaginatedChangeLog({
      versionCountPerPage: PAGINATION_VERSION_COUNT_PER_PAGE,
    });

    const totalPageCount = pageContentList.length;

    const currentPageIndex = getPageIndexFromQuery(
      context.query[PAGINATION_QUERY_NAME],
      totalPageCount,
    );
    const content = pageContentList[currentPageIndex];

    // 3. Extract table of contents from MDX
    const tree = remark().use(mdx).parse(content);
    const node = generateToc(tree, {maxDepth: 4});
    const tableOfContents = getMDXItems(node.map, {});

    // 4. Render MDX
    const mdxSource = await renderToString(content, {
      components,
      mdxOptions: {
        rehypePlugins,
      },
      scope: data,
    });

    return {
      props: {
        type: PageType.MDX,
        data: {
          mdxSource,
          frontMatter: data,
          tableOfContents,
          githubLink,
          asPath: '/changelog',
        },
        totalPageCount,
      },
    };
  } catch (err) {
    console.error(err);
    return {
      notFound: true,
    };
  }
};

/**
 * Return value is zero-indexed
 */
function getPageIndexFromQuery(rawQueryValue: string | string[], totalPageCount: number): number {
  let result = 0;

  if (typeof rawQueryValue === 'string') {
    const maybeIndex = parseInt(rawQueryValue);

    if (!isNaN(maybeIndex)) {
      result = Math.min(
        Math.max(
          maybeIndex - 1, // `?page=1` is the first page
          0,
        ),
        totalPageCount - 1, // `?page=totalPageCount` is the last page
      );
    }
  }

  return result;
}
