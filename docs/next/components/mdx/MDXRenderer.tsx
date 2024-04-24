import navigation from 'util/navigation';
import {usePath} from 'util/usePath';
import {SHOW_VERSION_NOTICE} from 'util/version';

import cx from 'classnames';
import Icons from 'components/Icons';
import VersionDropdown from 'components/VersionDropdown';
import MDXComponents, {SearchIndexContext} from 'components/mdx/MDXComponents';
import hydrate from 'next-mdx-remote/hydrate';
import {MdxRemote} from 'next-mdx-remote/types';
import {NextSeo} from 'next-seo';
import React from 'react';

// The next-mdx-remote types are outdated.
const components: MdxRemote.Components = MDXComponents as any;
const searchProvider: React.ReactNode = SearchIndexContext.Provider as any;

export type MDXData = {
  mdxSource: MdxRemote.Source;
  frontMatter: {
    title: string;
    description: string;
    noindex?: boolean;
  };
  searchIndex: any;
  tableOfContents: any;
  githubLink: string;
  asPath: string;
};

export const VersionNotice = () => {
  if (!SHOW_VERSION_NOTICE) {
    return null;
  }

  return (
    <div className="bg-yellow-100 mb-10 mt-6 mx-4 shadow sm:rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          You are viewing an unreleased or outdated version of the documentation
        </h3>
        <div className="mt-3 text-sm">
          <a
            href="https://docs.dagster.io"
            className="font-medium text-indigo-600 hover:text-indigo-500"
          >
            View Latest Documentation <span aria-hidden="true">→</span>
          </a>
        </div>
      </div>
    </div>
  );
};

const BreadcrumbNav = ({asPath}) => {
  const {asPathWithoutAnchor} = usePath();
  const pagePath = asPath ? asPath : asPathWithoutAnchor;

  function traverse(currNode, path, stack) {
    if (currNode.path === path) {
      return [...stack, currNode];
    }
    if (currNode.children === undefined) {
      return;
    }

    const childrenNodes = currNode.children;
    for (let i = 0; i < childrenNodes.length; i++) {
      const match = traverse(childrenNodes[i], path, [...stack, currNode]);
      if (match) {
        return match;
      }
    }
  }

  let breadcrumbItems = [];

  for (let i = 0; i < navigation.length; i++) {
    const matchedStack = traverse(navigation[i], pagePath, []);
    if (matchedStack) {
      breadcrumbItems = matchedStack;
      break;
    }
  }

  return (
    breadcrumbItems.length >= 1 && (
      <nav className="flex py-2" aria-label="Breadcrumb">
        <ol className="inline-flex">
          {breadcrumbItems.map((item, index) => {
            return (
              <li key={item.path || item.title}>
                <div className="flex items-center">
                  {index > 0 && (
                    <svg
                      className="w-3 h-3 text-gray-400 flex-shrink-0 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 20 20"
                    >
                      {Icons['ChevronRight']}
                    </svg>
                  )}
                  <a
                    href={item.path}
                    className={cx('mr-1 lg:mr-2 text-sm lg:font-normal text-gable-green truncate', {
                      // Map nav hierarchy to levels for docs search
                      'DocSearch-lvl0': index === 0,
                      'DocSearch-lvl1': index === 1,
                      'DocSearch-lvl2': index === 2,
                    })}
                  >
                    {item.title}
                  </a>
                </div>
              </li>
            );
          })}
        </ol>
      </nav>
    )
  );
};

export const VersionedContentLayout = ({children, asPath = null}) => {
  return (
    <div className="flex-1 w-full min-w-0 relative z-0 focus:outline-none" tabIndex={0}>
      <div
        className="flex flex-col lg:mt-5 max-w-7xl"
        style={{marginLeft: 'auto', marginRight: 'auto'}}
      >
        <div className="flex justify-between px-4 mb-4">
          <div className="flex justify-start flex-col lg:flex-row lg:px-4 w-full lg:items-center">
            <div className="flex pr-4">
              <VersionDropdown />
            </div>
            <BreadcrumbNav asPath={asPath} />
          </div>
        </div>
        <div className="flex flex-col">
          {/* Start main area*/}

          <VersionNotice />
          <div className="py-4 px-4 sm:px-6 lg:px-8 w-full">
            {children}
            <div className="mt-12 mb-12 border-t border-gray-200 px-4 flex items-center justify-between sm:px-0"></div>
          </div>
          {/* End main area */}
        </div>
      </div>
    </div>
  );
};

function VersionedMDXRenderer({data}: {data: MDXData}) {
  const {mdxSource, frontMatter, searchIndex} = data;

  const content = hydrate(mdxSource, {
    components,
    provider: {
      component: searchProvider,
      props: {value: searchIndex},
    },
  });

  return (
    <>
      <NextSeo
        title={frontMatter.title}
        description={frontMatter.description}
        openGraph={{
          title: frontMatter.title,
          description: frontMatter.description,
        }}
        noindex={frontMatter.noindex}
      />
      {content}
    </>
  );
}

export default VersionedMDXRenderer;
