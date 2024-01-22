import {promises as fs} from 'fs';
import path from 'path';
import {latestAllDynamicPaths} from 'util/navigation';
import zlib from 'zlib';

import {Shimmer} from 'components/Shimmer';
import {getMDXItems} from 'components/SidebarNavigation';
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

import MDXComponents, {SearchIndexContext} from '../components/mdx/MDXComponents';
import MDXRenderer, {MDXData, VersionedContentLayout} from '../components/mdx/MDXRenderer';
import {SphinxPrefix, sphinxPrefixFromPage} from '../util/useSphinx';

// The next-mdx-remote types are outdated.
const components: MdxRemote.Components = MDXComponents as any;
const searchProvider: React.ReactNode = SearchIndexContext.Provider as any;

type HTMLData = {
  body: string;
  toc: string;
  path: string;
};

enum PageType {
  MDX = 'MDX',
  HTML = 'HTML',
}

type Props =
  | {
      type: PageType.MDX;
      data: MDXData;
    }
  | {type: PageType.HTML; data: HTMLData};

function HTMLRenderer({data}: {data: HTMLData}) {
  const {body, toc, path} = data;
  const markup = {__html: body};
  const tocMarkup = {__html: toc};

  return (
    <>
      <VersionedContentLayout asPath={path}>
        <div
          className="DocSearch-content prose dark:prose-dark max-w-none"
          dangerouslySetInnerHTML={markup}
        />
      </VersionedContentLayout>

      <aside className="relative xl:block flex-none w-80 flex shrink-0 border-l border-gray-200">
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
  const router = useRouter();

  // If the page is not yet generated, this shimmer/skeleton will be displayed
  // initially until getStaticProps() finishes running
  if (router.isFallback) {
    return <Shimmer />;
  }

  return (
    <>
      {props.type === PageType.MDX ? (
        <MDXRenderer data={props.data} />
      ) : (
        <HTMLRenderer data={props.data} />
      )}
    </>
  );
}

async function getContent(asPath: string) {
  // render files from the local content folder
  const basePath = path.resolve('../content');
  const pathToFile = path.join(basePath, asPath);
  const buffer = await fs.readFile(pathToFile);
  const contentString = buffer.toString();
  return contentString;
}

async function getGzJsonContent(asPath: string) {
  const basePath = path.resolve('../content');
  const pathToFile = path.join(basePath, asPath);
  const buffer = await fs.readFile(pathToFile);
  return new Promise<any>((resolve, reject) => {
    zlib.gunzip(buffer, (err, result) => {
      if (err) {
        reject(err);
      }
      resolve(JSON.parse(result.toString()));
    });
  });
}

async function getSphinxData(sphinxPrefix: SphinxPrefix, path: string) {
  const page = path.split('/').splice(1);
  if (sphinxPrefix === SphinxPrefix.API_DOCS) {
    const {
      api: {apidocs: data},
    } = await getGzJsonContent('/api/sections.json.gz');

    let curr = data;
    for (const part of page) {
      curr = curr[part];
    }

    const {body, toc} = curr;

    return {
      props: {type: PageType.HTML, data: {body, toc, path: `/${SphinxPrefix.API_DOCS}${path}`}},
    };
  } else {
    const data = await getGzJsonContent('/api/modules.json.gz');
    let curr = data;
    for (const part of page) {
      curr = curr[part];
    }

    const {body} = curr;

    return {
      props: {type: PageType.HTML, data: {body, path: `/${SphinxPrefix.MODULES}${path}`}},
    };
  }
}

export const getStaticProps: GetStaticProps = async ({params}) => {
  const {page} = params;
  const asPath = Array.isArray(page) ? '/' + page.join('/') : page;

  const {sphinxPrefix, asPath: subPath} = sphinxPrefixFromPage(asPath);
  // If the subPath == "/", then we continue onto the MDX render to render the _apidocs.mdx page
  if (sphinxPrefix && subPath !== '/') {
    try {
      return getSphinxData(sphinxPrefix, subPath);
    } catch (err) {
      console.log(err);
      return {notFound: true};
    }
  }

  const githubLink = new URL(
    path.join('dagster-io/dagster/tree/master/docs/content', '/', asPath + '.mdx'),
    'https://github.com',
  ).href;

  try {
    // 1. Read and parse versioned search
    const searchIndex = await getGzJsonContent('/api/searchindex.json.gz');

    // 2. Read and parse versioned MDX content
    const source = await getContent(asPath + '.mdx');
    const {content, data} = matter(source);

    // 3. Extract table of contents from MDX
    const tree = remark().use(mdx).parse(content);
    const node = generateToc(tree, {maxDepth: 4});
    const tableOfContents = getMDXItems(node.map, {});

    // 4. Render MDX
    const mdxSource = await renderToString(content, {
      components,
      provider: {
        component: searchProvider,
        props: {value: searchIndex},
      },
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
          searchIndex,
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
    paths: latestAllDynamicPaths({excludeNonMdx: true}),
    fallback: true,
  };
}
