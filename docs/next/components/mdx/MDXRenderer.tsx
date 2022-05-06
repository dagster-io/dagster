import MDXComponents, {
  SearchIndexContext,
} from "components/mdx/MDXComponents";
import Pagination from "components/Pagination";
import Icons from "components/Icons";
import { VersionDropdown } from "components/VersionDropdown";

import { SphinxPrefix, sphinxPrefixFromPage } from "util/useSphinx";
import { useVersion, versionFromPage } from "util/useVersion";

import axios from "axios";
import { GetStaticProps } from "next";
import Link from "components/Link";
import { MdxRemote } from "next-mdx-remote/types";
import { NextSeo } from "next-seo";
import SidebarNavigation, { getItems } from "components/mdx/SidebarNavigation";
import { latestAllPaths } from "util/useNavigation";
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

import { Shimmer } from "components/Shimmer";

const components: MdxRemote.Components = MDXComponents;

export type MDXData = {
  mdxSource: MdxRemote.Source;
  frontMatter: {
    title: string;
    description: string;
  };
  searchIndex: any;
  tableOfContents: any;
  githubLink: string;
};

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
              stable. You can view the version of this page from our latest
              release below.
            </p>
          ) : (
            <p>
              This documentation is for an older version ({version}) of Dagster.
              You can view the version of this page from our latest release
              below.
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

const BreadcrumbNav = () => {
  const { asPathWithoutAnchor } = useVersion();
  console.log(asPathWithoutAnchor.split("/"));
  // TODO: HERE!!!!!!!!!!!!!
  return (
    <nav className="flex px-4 py-3" aria-label="Breadcrumb">
      <ol className="inline-flex space-x-1 md:space-x-3">
        <li className="inline-flex">
          <a
            href="#"
            className="inline-flex text-sm font-medium text-gray-700 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
          >
            Tutorial
          </a>
        </li>
        <li>
          <div className="flex items-center">
            <svg
              className="w-3 h-3 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 20 20"
              xmlns="http://www.w3.org/2000/svg"
            >
              {Icons["ChevronRight"]}
            </svg>
            <a
              href="#"
              className="ml-1 text-sm font-medium text-gray-700 hover:text-gray-900 md:ml-2 dark:text-gray-400 dark:hover:text-white"
            >
              Intro Tutorial
            </a>
          </div>
        </li>
        <li aria-current="page">
          <div className="flex items-center">
            <svg
              className="w-3 h-3 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 20 20"
              xmlns="http://www.w3.org/2000/svg"
            >
              {Icons["ChevronRight"]}
            </svg>
            <span className="ml-1 text-sm font-medium text-gray-400 md:ml-2 dark:text-gray-500">
              Setup for the Tutorial
            </span>
          </div>
        </li>
      </ol>
    </nav>
  );
};

export const VersionedContentLayout = ({ content }) => {
  return (
    <div
      className="flex-1 min-w-0 relative z-0 focus:outline-none pt-4"
      tabIndex={0}
    >
      <div className="mt-5 flex flex-col">
        <div className="flex justify-between px-4">
          <div className="flex justify-start px-4">
            <div className="flex">
              <VersionDropdown />
            </div>
            <div className="flex">
              <BreadcrumbNav />
            </div>
          </div>

          <div className="flex-none">
            <button
              // onClick={}
              className="hidden lg:inline-block px-2 py-2 ml-2 text-sm rounded-full border border-gray-300 text-gray-600 hover:text-gray-700 hover:bg-white transition-colors duration-200"
            >
              Share Feedback
            </button>
          </div>
        </div>
        <div className="flex flex-row">
          {/* Start main area*/}

          <VersionNotice />
          <div className="py-4 px-4 sm:px-6 lg:px-8 w-full">
            <div className="DocSearch-content prose dark:prose-dark max-w-none">
              {content}
            </div>
            <Pagination />
          </div>
          {/* End main area */}
        </div>
      </div>
    </div>
  );
};

export function UnversionedMDXRenderer({ data }: { data: MDXData }) {
  const { query } = useRouter();
  const { editMode } = query;

  const { mdxSource, frontMatter, searchIndex, tableOfContents, githubLink } =
    data;

  const content = hydrate(mdxSource, {
    components,
    provider: {
      component: SearchIndexContext.Provider,
      props: { value: searchIndex },
    },
  });
  const navigationItems = tableOfContents.items.filter((item) => item?.items);

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
      <div
        className="flex-1 min-w-0 relative z-0 focus:outline-none pt-4"
        tabIndex={0}
      >
        <div className="flex flex-row pb-8">
          {/* Start main area*/}

          <div className="py-4 px-4 sm:px-6 lg:px-8 w-full">
            <div className="DocSearch-content prose dark:prose-dark max-w-none">
              {content}
            </div>
          </div>
          {/* End main area */}
        </div>
      </div>

      {!editMode && (
        <aside className="hidden relative xl:block flex-none w-96 flex shrink-0 border-gray-200">
          {/* Start secondary column (hidden on smaller screens) */}
          <div className="flex flex-col justify-between sticky top-24  py-6 px-4 sm:px-6 lg:px-8">
            <div className="mb-8 border border-gray-100 rounded-lg px-4 py-2 relative overflow-y-scroll max-h-(screen-60)">
              <div className="font-semibold text-gable-green">On This Page</div>
              <div className="mt-6">
                {navigationItems && (
                  <SidebarNavigation items={navigationItems} />
                )}
              </div>
            </div>

            <div className="mb-8 border border-gray-100 rounded-lg px-4 py-4 relative overflow-y-scroll max-h-(screen-60)">
              <div className="flex items-center group">
                <svg
                  className="h-4 w-4 text-gray-500 dark:text-gray-300 group-hover:text-gray-800 dark:group-hover:text-gray-100 transition transform group-hover:scale-105 group-hover:rotate-6"
                  role="img"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <title>GitHub icon</title>
                  <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
                </svg>
                <a
                  className="ml-2 font-semibold text-md text-gray-500 dark:text-gray-300 group-hover:text-gray-800 dark:group-hover:text-gray-100"
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

function VersionedMDXRenderer({ data }: { data: MDXData }) {
  const { query } = useRouter();
  const { editMode } = query;

  const { mdxSource, frontMatter, searchIndex, tableOfContents, githubLink } =
    data;

  const content = hydrate(mdxSource, {
    components,
    provider: {
      component: SearchIndexContext.Provider,
      props: { value: searchIndex },
    },
  });
  const navigationItems = tableOfContents.items.filter((item) => item?.items);

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

      <VersionedContentLayout content={content} />

      {!editMode && (
        <aside className="hidden relative xl:block flex-none w-96 flex shrink-0 border-gray-200">
          {/* Start secondary column (hidden on smaller screens) */}
          <div className="flex flex-col justify-between sticky top-24  py-6 px-4 sm:px-6 lg:px-8">
            <div className="mb-8 border border-gray-100 rounded-lg px-4 py-2 relative overflow-y-scroll max-h-(screen-60)">
              <div className="font-semibold text-gable-green">On This Page</div>
              <div className="mt-6">
                {navigationItems && (
                  <SidebarNavigation items={navigationItems} />
                )}
              </div>
            </div>

            <div className="mb-8 border border-gray-100 rounded-lg px-4 py-4 relative overflow-y-scroll max-h-(screen-60)">
              <div className="flex items-center group">
                <svg
                  className="h-4 w-4 text-gray-500 dark:text-gray-300 group-hover:text-gray-800 dark:group-hover:text-gray-100 transition transform group-hover:scale-105 group-hover:rotate-6"
                  role="img"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <title>GitHub icon</title>
                  <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
                </svg>
                <a
                  className="ml-2 font-semibold text-md text-gray-500 dark:text-gray-300 group-hover:text-gray-800 dark:group-hover:text-gray-100"
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

export default VersionedMDXRenderer;
