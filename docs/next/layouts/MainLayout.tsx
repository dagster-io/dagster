import React, { useEffect, useState } from "react";

import Link from "next/link";
import Pagination from "components/Pagination";
import Sidebar from "../components/Sidebar";
import { useRouter } from "next/router";

const VersionNotice = () => {
  const {
    asPath,
    locale: version,
    defaultLocale: defaultVersion,
  } = useRouter();

  if (version == defaultVersion) {
    return null;
  }

  return (
    <div className="bg-yellow-100 mb-10 shadow sm:rounded-lg">
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

const Header = () => {
  return (
    <div className="sticky top-0 z-30 flex items-center bg-white border-b">
      <div
        className="flex-1 relative z-0 cursor-pointer focus:outline-none"
        tabIndex={0}
      >
        {/* Search Bar*/}
        <div className="px-4 sm:px-6 lg:px-8 h-16 flex items-center text-gray-700 hover:bg-gray-50">
          <svg
            className="h-5 w-5"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
              clipRule="evenodd"
            />
          </svg>
          <div className="ml-4 hover:text-gray-900">
            Quick search <span className="hidden sm:inline">for anything</span>{" "}
            <span className="hidden lg:inline-block px-2 py-1 ml-2 text-gray-500 text-sm border border-gray-200 rounded-md">
              ⌘K
            </span>
          </div>
        </div>
        {/* End Search Bar */}
      </div>
      <div className="relative xl:w-96">
        {/* Start secondary column */}
        <div className="px-4 sm:px-6 lg:px-8 flex space-x-6 items-center">
          {/* Github Icon */}
          <a href="https://github.com/dagster-io/dagster">
            <svg
              className="h-6 w-6 text-gray-400 hover:text-gray-900"
              role="img"
              viewBox="0 0 24 24"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              <title>GitHub icon</title>
              <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
            </svg>
          </a>
          <a href="https://github.com/dagster-io/dagster">
            <svg
              className="h-6 w-6 text-gray-400 hover:text-yellow-500"
              role="img"
              viewBox="0 0 24 24"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              <title>Stack Overflow icon</title>
              <path d="M18.986 21.865v-6.404h2.134V24H1.844v-8.539h2.13v6.404h15.012zM6.111 19.731H16.85v-2.137H6.111v2.137zm.259-4.852l10.48 2.189.451-2.07-10.478-2.187-.453 2.068zm1.359-5.056l9.705 4.53.903-1.95-9.706-4.53-.902 1.936v.014zm2.715-4.785l8.217 6.855 1.359-1.62-8.216-6.853-1.35 1.617-.01.001zM15.751 0l-1.746 1.294 6.405 8.604 1.746-1.294L15.749 0h.002z" />
            </svg>
          </a>
          <a href="https://github.com/dagster-io/dagster">
            <svg
              className="h-6 w-6 text-gray-400 hover:text-pink-500"
              role="img"
              viewBox="0 0 24 24"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              <title>Slack icon</title>
              <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z" />
            </svg>
          </a>
          <a href="https://github.com/dagster-io/dagster">
            <svg
              className="h-7 w-7 text-gray-400 hover:text-blue-500"
              role="img"
              viewBox="0 0 20 20"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"></path>
              <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"></path>
            </svg>
          </a>
        </div>
        {/* End secondary column */}
      </div>
    </div>
  );
};

const Layout = ({ children }) => {
  return (
    <div className="h-screen flex overflow-hidden bg-white">
      <Sidebar />
      <div className="w-full overflow-y-scroll">
        <div className="max-w-7xl mx-auto">
          <div className="relative w-full">
            <div className="lg:hidden">
              <div className="flex items-center justify-between bg-gray-50 border-b border-gray-200 px-4 py-1.5">
                <div>
                  <img
                    className="h-8 w-auto"
                    src="https://tailwindui.com/img/logos/workflow-mark-indigo-600.svg"
                    alt="Workflow"
                  />
                </div>
                <div>
                  <button
                    type="button"
                    className="-mr-3 h-12 w-12 inline-flex items-center justify-center rounded-md text-gray-500 hover:text-gray-900"
                  >
                    <span className="sr-only">Open sidebar</span>
                    {/* Heroicon name: menu */}
                    <svg
                      className="h-6 w-6"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 6h16M4 12h16M4 18h16"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            <Header />
            <div className="w-full relative z-0 flex justify-center">
              <VersionNotice />
              {children}
            </div>
          </div>

          <div className="pb-24">
            <Pagination />
          </div>
        </div>
      </div>
    </div>
  );
};

export const getLayout = (page) => <Layout>{page}</Layout>;

export default Layout;
