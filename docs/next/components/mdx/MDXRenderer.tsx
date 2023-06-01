import {useNavigation} from 'util/useNavigation';
import {useVersion} from 'util/useVersion';

import cx from 'classnames';
import Icons from 'components/Icons';
import Link from 'components/Link';
import {RightSidebar} from 'components/SidebarNavigation';
import VersionDropdown from 'components/VersionDropdown';
import MDXComponents, {SearchIndexContext} from 'components/mdx/MDXComponents';
import hydrate from 'next-mdx-remote/hydrate';
import {MdxRemote} from 'next-mdx-remote/types';
import {NextSeo} from 'next-seo';
import {useRouter} from 'next/router';
import React from 'react';

const components: MdxRemote.Components = MDXComponents;

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
  const {asPath, version, defaultVersion} = useVersion();

  if (version === defaultVersion) {
    return null;
  }

  return (
    <div className="bg-yellow-100 mb-10 mt-6 mx-4 shadow sm:rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          {version === 'master'
            ? 'You are viewing an unreleased version of the documentation.'
            : 'You are viewing an outdated version of the documentation.'}
        </h3>
        <div className="mt-2 text-sm text-gray-500">
          {version === 'master' ? (
            <p>
              This documentation is for an unreleased version ({version}) of Dagster. The content
              here is not guaranteed to be correct or stable. You can view the version of this page
              from our latest release below.
            </p>
          ) : (
            <p>
              This documentation is for an older version ({version}) of Dagster. You can view the
              version of this page from our latest release below.
            </p>
          )}
        </div>
        <div className="mt-3 text-sm">
          <Link href={asPath} version={defaultVersion}>
            <a className="font-medium text-indigo-600 hover:text-indigo-500">
              {' '}
              View Latest Documentation <span aria-hidden="true">→</span>
            </a>
          </Link>
        </div>
      </div>
    </div>
  );
};

const BreadcrumbNav = ({asPath}) => {
  const {asPathWithoutAnchor} = useVersion();
  const pagePath = asPath ? asPath : asPathWithoutAnchor;

  const navigation = useNavigation();

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
    breadcrumbItems.length > 1 && (
      <nav className="flex flex-nowrap lg:px-4 py-2" aria-label="Breadcrumb">
        <ol className="md:inline-flex space-x-1 lg:space-x-3">
          {breadcrumbItems.map((item, index) => {
            return (
              <li key={item.path || item.title}>
                <div className="flex flex-nowrap items-center">
                  {index > 0 && (
                    <svg
                      className="w-3 h-3 text-gray-400 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 20 20"
                    >
                      {Icons['ChevronRight']}
                    </svg>
                  )}
                  <a
                    href={item.path}
                    className={cx(
                      'ml-1 lg:ml-2 text-xs lg:text-sm lg:font-normal text-gable-green truncate',
                      {
                        // Map nav hierarchy to levels for docs search
                        'DocSearch-lvl0': index === 0,
                        'DocSearch-lvl1': index === 1,
                        'DocSearch-lvl2': index === 2,
                      },
                    )}
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
          <div className="flex justify-start flex-col lg:flex-row lg:px-4 w-full">
            <div className="flex">
              <VersionDropdown />
            </div>
            <div className="flex">
              <BreadcrumbNav asPath={asPath} />
            </div>
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

export function UnversionedMDXRenderer({
  data,
  toggleFeedback,
  bottomContent,
}: {
  data: MDXData;
  toggleFeedback: any;
  bottomContent?: React.ReactNode | null;
}) {
  const {query} = useRouter();
  const {editMode} = query;

  const {mdxSource, frontMatter, searchIndex, tableOfContents, githubLink} = data;

  const content = hydrate(mdxSource, {
    components,
    provider: {
      component: SearchIndexContext.Provider,
      props: {value: searchIndex},
    },
  });
  const navigationItemsForMDX = tableOfContents.items.filter((item) => item?.items);

  return (
    <>
      <NextSeo
        title={frontMatter.title}
        description={frontMatter.description}
        openGraph={{
          title: frontMatter.title,
          description: frontMatter.description,
        }}
      />
      <div className="flex-1 min-w-0 relative z-0 focus:outline-none pt-4" tabIndex={0}>
        <div
          className="flex flex-row pb-8 max-w-7xl"
          style={{marginLeft: 'auto', marginRight: 'auto'}}
        >
          {/* Start main area*/}

          <div className="py-4 px-4 sm:px-6 lg:px-8 w-full">
            <div className="DocSearch-content prose dark:prose-dark max-w-none">{content}</div>
            {bottomContent ?? null}
          </div>
          {/* End main area */}
        </div>
      </div>

      <RightSidebar
        editMode={editMode}
        navigationItemsForMDX={navigationItemsForMDX}
        githubLink={githubLink}
        toggleFeedback={toggleFeedback}
      />
    </>
  );
}

function VersionedMDXRenderer({data}: {data: MDXData}) {
  const {mdxSource, frontMatter, searchIndex} = data;

  const content = hydrate(mdxSource, {
    components,
    provider: {
      component: SearchIndexContext.Provider,
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
