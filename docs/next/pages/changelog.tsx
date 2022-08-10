import {promises as fs} from 'fs';
import path from 'path';

import {Shimmer} from 'components/Shimmer';
import rehypePlugins from 'components/mdx/rehypePlugins';
import matter from 'gray-matter';
import generateToc from 'mdast-util-toc';
import {GetStaticProps} from 'next';
import renderToString from 'next-mdx-remote/render-to-string';
import {MdxRemote} from 'next-mdx-remote/types';
import {useRouter} from 'next/router';
import React from 'react';
import remark from 'remark';
import mdx from 'remark-mdx';
import visit from 'unist-util-visit';

import FeedbackModal from '../components/FeedbackModal';
import MDXComponents from '../components/mdx/MDXComponents';
import {MDXData, UnversionedMDXRenderer} from '../components/mdx/MDXRenderer';

const components: MdxRemote.Components = MDXComponents;

enum PageType {
  MDX = 'MDX',
}

type Props = {
  type: PageType.MDX;
  data: MDXData;
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

  return (
    <>
      <FeedbackModal isOpen={isFeedbackOpen} closeFeedback={closeFeedback} />
      <UnversionedMDXRenderer data={props.data} toggleFeedback={toggleFeedback} />
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
        current.url = item['url'];
      }
      if (item.type === `text`) {
        current.title = item['value'];
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
    path.join('dagster-io/dagster/blob/master/CHANGES.md'),
    'https://github.com',
  ).href;
  const pathToMdxFile = path.resolve('../../CHANGES.md');

  try {
    // 2. Read and parse versioned MDX content
    const source = await fs.readFile(pathToMdxFile);
    const {content, data} = matter(source);

    // 3. Extract table of contents from MDX
    const tree = remark().use(mdx).parse(content);
    const node = generateToc(tree, {maxDepth: 4});
    const tableOfContents = getItems(node.map, {});

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
