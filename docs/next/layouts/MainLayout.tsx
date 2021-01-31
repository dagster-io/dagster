import React, { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import { useRouter } from "next/router";
import Link from "next/link";

const SearchBar = ({ openSearch, setSearchTerm }) => {
  return (
    <div className="flex-1 flex justify-center lg:justify-end mb-10">
      <div className="w-full ">
        <label htmlFor="search" className="sr-only">
          Search Docs
        </label>
        <div className="relative text-gray-400 focus-within:text-gray-400">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            {/* Heroicon name: search */}
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
          </div>
          <input
            id="search"
            name="search"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-gray-300 bg-opacity-25 text-gray-800 placeholder-gray-700 focus:outline-none focus:bg-white focus:ring-0 focus:placeholder-gray-400 focus:text-gray-900 sm:text-sm"
            placeholder="Search docs"
            type="search"
            onChange={(event) => setSearchTerm(event.target.value)}
            onFocus={openSearch}
          />
        </div>
      </div>
    </div>
  );
};

const RandomResult = ({ searchTerm }) => {
  const front = Math.floor(Math.random() * 6) + 1;
  const back = Math.floor(Math.random() * 6) + 1;

  return (
    <a href="#" className="block py-2 px-4 hover:bg-gray-200">
      <span className="bg-yellow-200">{searchTerm}</span>{" "}
    </a>
  );
};

const SearchResults = ({ searchTerm }) => {
  const results = Math.floor(Math.random() * 40) + 1;

  return (
    <>
      <div className="bg-gray-100 py-2 rounded-md">
        <div>
          <div className="sm:hidden">
            <label htmlFor="tabs" className="sr-only">
              Select a tab
            </label>
            <select
              id="tabs"
              name="tabs"
              className="block w-full focus:ring-indigo-500 focus:border-indigo-500 border-gray-300 rounded-md"
            >
              <option>Documentation</option>
              <option selected>API Reference</option>
            </select>
          </div>
          <div className="hidden sm:block">
            <div className="flex">
              <nav className="flex flex-1 space-x-4" aria-label="Tabs">
                <a
                  href="#"
                  className="text-gray-500 hover:text-gray-700 px-3 py-2 font-medium text-sm rounded-md"
                >
                  Documentation
                </a>
                {/* Current: "bg-indigo-100 text-indigo-700", Default: "text-gray-500 hover:text-gray-700" */}
                <a
                  href="#"
                  className="bg-indigo-100 text-indigo-700 px-3 py-2 font-medium text-sm rounded-md"
                  aria-current="page"
                >
                  API Reference
                </a>
                <a
                  href="#"
                  className="text-gray-500 hover:text-gray-700 px-3 py-2 font-medium text-sm rounded-md"
                >
                  Glossary
                </a>
              </nav>
              <div className="mr-4">
                <div
                  className="px-3 py-2 font-medium text-sm rounded-md"
                  aria-current="page"
                >
                  {results} Results
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="mt-4 bg-gray-100 py-2 rounded-md">
        {[...Array(results)].map((i) => (
          <RandomResult searchTerm={searchTerm} />
        ))}
      </div>
    </>
  );
};

const FeedbackModal = ({ closeFeedback }: { closeFeedback: () => void }) => {
  const { asPath } = useRouter();
  const [currentPage, setCurrentPage] = useState<string>(asPath);

  return (
    <div className="fixed inset-0 overflow-hidden z-10">
      <div className="absolute inset-0 overflow-hidden">
        <section
          className="absolute inset-y-0 pl-16 max-w-full right-0 flex"
          aria-labelledby="slide-over-heading"
        >
          {/*
  Slide-over panel, show/hide based on slide-over state.

  Entering: "transform transition ease-in-out duration-500 sm:duration-700"
    From: "translate-x-full"
    To: "translate-x-0"
  Leaving: "transform transition ease-in-out duration-500 sm:duration-700"
    From: "translate-x-0"
    To: "translate-x-full"
*/}
          <div className="w-screen max-w-md">
            <form className="h-full divide-y divide-gray-200 flex flex-col bg-white shadow-xl">
              <div className="flex-1 h-0 overflow-y-auto">
                <div className="py-6 px-4 bg-indigo-700 sm:px-6">
                  <div className="flex items-center justify-between">
                    <h2
                      id="slide-over-heading"
                      className="text-lg font-medium text-white"
                    >
                      Submit Feedback
                    </h2>
                    <div className="ml-3 h-7 flex items-center">
                      <button
                        onClick={closeFeedback}
                        className="bg-indigo-700 rounded-md text-indigo-200 hover:text-white focus:outline-none focus:ring-2 focus:ring-white"
                      >
                        <span className="sr-only">Close panel</span>
                        {/* Heroicon name: x */}
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
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      </button>
                    </div>
                  </div>
                  <div className="mt-1">
                    <p className="text-sm text-indigo-300">
                      Feedback helps us improve our documentation so you can be
                      more productive. Please let us know about anything!
                    </p>
                  </div>
                </div>
                <div className="flex-1 flex flex-col justify-between">
                  <div className="px-4 divide-y divide-gray-200 sm:px-6">
                    <div className="space-y-6 pt-6 pb-5">
                      <div>
                        <label
                          htmlFor="project_name"
                          className="block text-sm font-medium text-gray-900"
                        >
                          Current Page
                        </label>
                        <div className="mt-1">
                          <input
                            type="text"
                            name="project_name"
                            id="project_name"
                            className="block w-full shadow-sm sm:text-sm focus:ring-indigo-500 focus:border-indigo-500 border-gray-300 rounded-md"
                            value={currentPage}
                            onChange={(event) =>
                              setCurrentPage(event.target.value)
                            }
                          />
                        </div>
                      </div>
                      <div>
                        <label
                          htmlFor="description"
                          className="block text-sm font-medium text-gray-900"
                        >
                          Description
                        </label>
                        <div className="mt-1">
                          <textarea
                            id="description"
                            name="description"
                            rows={4}
                            className="block w-full shadow-sm sm:text-sm focus:ring-indigo-500 focus:border-indigo-500 border-gray-300 rounded-md"
                            defaultValue={""}
                          />
                        </div>
                      </div>

                      <fieldset>
                        <legend className="sr-only">
                          Submit as Public Github Issue
                        </legend>
                        <div className="bg-white rounded-md -space-y-px">
                          {/* On: "bg-indigo-50 border-indigo-200 z-10", Off: "border-gray-200" */}
                          <div className="relative border rounded-tl-md rounded-tr-md p-4 flex">
                            <div className="flex items-center h-5">
                              <input
                                id="settings-option-0"
                                name="privacy_setting"
                                type="radio"
                                className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 cursor-pointer border-gray-300"
                                defaultChecked
                              />
                            </div>
                            <label
                              htmlFor="settings-option-0"
                              className="ml-3 flex flex-col cursor-pointer"
                            >
                              {/* On: "text-indigo-900", Off: "text-gray-900" */}
                              <span className="block text-sm font-medium">
                                Submit as public Github Issue
                              </span>
                              {/* On: "text-indigo-700", Off: "text-gray-500" */}
                              <span className="block text-sm">
                                Submit this feedback to our public issue tracker
                                at{" "}
                                <a href="#" className="underline">
                                  https://github.com/dagster-io/dagster/issues
                                </a>
                              </span>
                            </label>
                          </div>
                          {/* On: "bg-indigo-50 border-indigo-200 z-10", Off: "border-gray-200" */}
                          <div className="relative border border-gray-200 p-4 flex">
                            <div className="flex items-center h-5">
                              <input
                                id="settings-option-1"
                                name="privacy_setting"
                                type="radio"
                                className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 cursor-pointer border-gray-300"
                              />
                            </div>
                            <label
                              htmlFor="settings-option-1"
                              className="ml-3 flex flex-col cursor-pointer"
                            >
                              {/* On: "text-indigo-900", Off: "text-gray-900" */}
                              <span className="block text-sm font-medium">
                                Private to Dagster Team
                              </span>
                              {/* On: "text-indigo-700", Off: "text-gray-500" */}
                              <span className="block text-sm">
                                Send this feedback privately to the Dagster team
                              </span>
                            </label>
                          </div>
                          {/* On: "bg-indigo-50 border-indigo-200 z-10", Off: "border-gray-200" */}
                        </div>
                      </fieldset>

                      <div>
                        <label
                          htmlFor="project_name"
                          className="block text-sm font-medium text-gray-900"
                        >
                          Your Github Handle (Optional)
                        </label>
                        <div className="mt-1">
                          <input
                            type="text"
                            name="project_name"
                            id="project_name"
                            className="block w-full shadow-sm sm:text-sm focus:ring-indigo-500 focus:border-indigo-500 border-gray-300 rounded-md"
                            placeholder="@yourusername"
                          />
                        </div>
                      </div>

                      <div>
                        <label
                          htmlFor="project_name"
                          className="block text-sm font-medium text-gray-900"
                        >
                          Your Email (Optional)
                        </label>
                        <div className="mt-1">
                          <input
                            type="text"
                            name="project_name"
                            id="project_name"
                            className="block w-full shadow-sm sm:text-sm focus:ring-indigo-500 focus:border-indigo-500 border-gray-300 rounded-md"
                            placeholder="@yourusername"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex-shrink-0 px-4 py-4 flex justify-end">
                <button
                  type="button"
                  className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="ml-4 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Submit Feedback
                </button>
              </div>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
};

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

const Layout = ({ children }) => {
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [openFeedback, setOpenFeedback] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const { locale: version, defaultLocale: defaultVersion } = useRouter();

  const openSearch = () => {
    setIsSearching(true);
  };

  const closeSearch = () => {
    setIsSearching(false);
  };

  const closeFeedback = () => {
    setOpenFeedback(false);
  };

  useEffect(() => {
    if (searchTerm.length > 0) {
      openSearch();
    } else {
      closeSearch();
    }
  }, [searchTerm]);

  return (
    <>
      {openFeedback && <FeedbackModal closeFeedback={closeFeedback} />}
      <div className="h-screen flex overflow-hidden bg-white">
        <Sidebar />
        <main
          className="flex-1 overflow-y-auto focus:outline-none"
          tabIndex={0}
        >
          <div className="relative max-w-7xl mx-auto md:px-8 xl:px-0">
            <div className="pt-10 pb-16">
              <div className="px-4 sm:px-6 md:px-0 static">
                <div className="flex space-x-4 items-baseline">
                  <div className="flex-1">
                    <SearchBar
                      openSearch={openSearch}
                      setSearchTerm={setSearchTerm}
                    />
                  </div>
                  <button
                    onClick={() => setOpenFeedback(true)}
                    className="flex items-center px-4 py-2 rounded-md hover:text-blue-500 hover:bg-gray-100 hover:font-semibold"
                  >
                    <svg
                      className="mr-2 -mt-1 h-4 w-4 text-gray-400 hover:text-blue-500"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"
                      ></path>
                    </svg>
                    Feedback?
                  </button>
                </div>
                {isSearching ? (
                  <SearchResults searchTerm={searchTerm} />
                ) : (
                  <>
                    <VersionNotice />
                    {children}
                  </>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
};

export const getLayout = (page) => <Layout>{page}</Layout>;

export default Layout;
