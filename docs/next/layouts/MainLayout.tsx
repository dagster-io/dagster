import React, { useEffect, useState } from "react";

import { Search } from "components/Search";
import Sidebar from "../components/Sidebar";
import { Transition } from "@headlessui/react";
import cx from "classnames";
import newGithubIssueUrl from "new-github-issue-url";
import { useLocalStorage } from "react-use";
import { useVersion } from "../util/useVersion";

export const FeedbackModal = ({
  isOpen,
  closeFeedback,
}: {
  isOpen: boolean;
  closeFeedback: () => void;
}) => {
  const { asPath, version } = useVersion();
  const [currentPage, setCurrentPage] = useState<string>(asPath);
  const [currentVersion, setCurrentVersion] = useState<string>(version);
  const [description, setDescription] = useState<string>("");
  const [title, setTitle] = useState<string>("");
  const [submitOption, setSubmitOption] = useState<string>("GH");

  const enablePrivateSubmition = false;

  useEffect(() => {
    setCurrentVersion(version);
    setCurrentPage(asPath);
    setTitle(`Problem on ${asPath} page`);
  }, [asPath, version]);

  const submitFeedback = (e) => {
    e.preventDefault();

    const url = newGithubIssueUrl({
      user: "dagster-io",
      repo: "dagster",
      title: `[Documentation Feedback] ${title}`,
      body: description,
      labels: ["documentation"],
    });

    window.open(url, "_blank");
    closeFeedback();
  };

  return (
    <Transition show={isOpen}>
      <section
        className="absolute inset-y-0 pl-16 max-w-full right-0 flex z-50"
        aria-labelledby="slide-over-heading"
      >
        <Transition.Child
          enter="transform transition ease-in-out duration-100 sm:duration-200"
          enterFrom="translate-x-full"
          enterTo="translate-x-0"
          leave="transform transition ease-in-out duration-100 sm:duration-200"
          leaveFrom="translate-x-0"
          leaveTo="translate-x-full"
        >
          <div className="w-screen max-w-md h-full">
            <form className="h-full divide-y divide-gray-200 flex flex-col bg-gray-100 shadow-xl">
              <div className="flex-1 h-0 overflow-y-auto">
                <div className="py-6 px-4 bg-gray-800 sm:px-6">
                  <div className="flex items-center justify-between">
                    <h2
                      id="slide-over-heading"
                      className="text-lg font-medium text-white"
                    >
                      Submit Feedback
                    </h2>
                    <div className="ml-3 h-7 flex items-center">
                      <button
                        type="button"
                        onClick={closeFeedback}
                        className="bg-gray-700 rounded-md text-gray-200 hover:text-white focus:outline-none focus:ring-2 focus:ring-white"
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
                  <div className="mt-6">
                    <p className="text-sm text-gray-300">
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
                          Page
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
                          htmlFor="project_name"
                          className="block text-sm font-medium text-gray-900"
                        >
                          Documentation Version
                        </label>
                        <div className="mt-1">
                          <input
                            type="text"
                            name="project_name"
                            id="project_name"
                            className="block w-full shadow-sm sm:text-sm focus:ring-indigo-500 focus:border-indigo-500 border-gray-300 rounded-md"
                            value={currentVersion}
                            onChange={(event) =>
                              setCurrentVersion(event.target.value)
                            }
                          />
                        </div>
                      </div>

                      <div>
                        <label
                          htmlFor="project_name"
                          className="block text-sm font-medium text-gray-900"
                        >
                          Issue Title
                        </label>
                        <div className="mt-1">
                          <input
                            type="text"
                            name="project_name"
                            id="project_name"
                            className="block w-full shadow-sm sm:text-sm focus:ring-indigo-500 focus:border-indigo-500 border-gray-300 rounded-md"
                            value={title}
                            onChange={(event) => setTitle(event.target.value)}
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
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                          />
                        </div>
                      </div>

                      {enablePrivateSubmition && (
                        <>
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
                                    name="gh_setting"
                                    value="GH"
                                    type="radio"
                                    className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 cursor-pointer border-gray-300"
                                    defaultChecked
                                    checked={submitOption === "GH"}
                                    onChange={(e) =>
                                      setSubmitOption(e.target.value)
                                    }
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
                                    Submit this feedback to our public issue
                                    tracker at{" "}
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
                                    name="private_setting"
                                    value="Private"
                                    type="radio"
                                    className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 cursor-pointer border-gray-300"
                                    checked={submitOption === "Private"}
                                    onChange={(e) =>
                                      setSubmitOption(e.target.value)
                                    }
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
                                    Send this feedback privately to the Dagster
                                    team
                                  </span>
                                </label>
                              </div>
                              {/* On: "bg-indigo-50 border-indigo-200 z-10", Off: "border-gray-200" */}
                            </div>
                          </fieldset>

                          {submitOption == "Private" && (
                            <>
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
                            </>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex-shrink-0 px-4 py-4 flex justify-end">
                <button
                  type="button"
                  onClick={closeFeedback}
                  className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Cancel
                </button>
                <button
                  onClick={submitFeedback}
                  className="ml-4 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Submit Feedback as GH Issue
                </button>
              </div>
            </form>
          </div>
        </Transition.Child>
      </section>
    </Transition>
  );
};

const Header = ({ openFeedback, isDarkMode, setDarkMode }) => {
  return (
    <div className="sticky top-0 z-30 flex items-center bg-white dark:bg-gray-900 border-b overflow-x-auto">
      <div
        className="flex-1 relative z-0 cursor-pointer focus:outline-none"
        tabIndex={0}
      >
        {/* Search Bar*/}
        <div className="px-4 sm:px-6 lg:px-8 h-16 flex justify-between items-center">
          <div className="flex items-center">
            <Search />
          </div>
          <div>
            <button
              onClick={openFeedback}
              className="hidden lg:inline-block px-2 py-1 ml-2 text-gray-500 dark:text-gray-300 text-sm border border-gray-200 dark:border-gray-500 rounded-md hover:bg-gray-100"
            >
              Share Feedback
            </button>
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
              className="h-6 w-6 text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 transition transform hover:scale-105 hover:rotate-6"
              role="img"
              viewBox="0 0 24 24"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              <title>GitHub icon</title>
              <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
            </svg>
          </a>
          <a href="https://dagster-slackin.herokuapp.com/">
            <svg
              className="h-6 w-6 text-gray-400 hover:text-pink-500 transition transform hover:scale-105 hover:rotate-6"
              role="img"
              viewBox="0 0 24 24"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              <title>Slack icon</title>
              <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z" />
            </svg>
          </a>
          <a href="https://twitter.com/dagsterio">
            <svg
              className="h-7 w-7 text-gray-400 hover:text-blue-300 transition transform hover:scale-105 hover:rotate-6"
              role="img"
              viewBox="0 0 24 24"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              <title>Twitter icon</title>
              <path d="M22.46,6C21.69,6.35 20.86,6.58 20,6.69C20.88,6.16 21.56,5.32 21.88,4.31C21.05,4.81 20.13,5.16 19.16,5.36C18.37,4.5 17.26,4 16,4C13.65,4 11.73,5.92 11.73,8.29C11.73,8.63 11.77,8.96 11.84,9.27C8.28,9.09 5.11,7.38 3,4.79C2.63,5.42 2.42,6.16 2.42,6.94C2.42,8.43 3.17,9.75 4.33,10.5C3.62,10.5 2.96,10.3 2.38,10C2.38,10 2.38,10 2.38,10.03C2.38,12.11 3.86,13.85 5.82,14.24C5.46,14.34 5.08,14.39 4.69,14.39C4.42,14.39 4.15,14.36 3.89,14.31C4.43,16 6,17.26 7.89,17.29C6.43,18.45 4.58,19.13 2.56,19.13C2.22,19.13 1.88,19.11 1.54,19.07C3.44,20.29 5.7,21 8.12,21C16,21 20.33,14.46 20.33,8.79C20.33,8.6 20.33,8.42 20.32,8.23C21.16,7.63 21.88,6.87 22.46,6Z" />
            </svg>
          </a>
          <a href="https://stackoverflow.com/questions/tagged/dagster">
            <svg
              className="h-6 w-6 text-gray-400 hover:text-yellow-500 transition transform hover:scale-105 hover:rotate-6"
              role="img"
              viewBox="0 0 24 24"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              <title>Stack Overflow icon</title>
              <path d="M18.986 21.865v-6.404h2.134V24H1.844v-8.539h2.13v6.404h15.012zM6.111 19.731H16.85v-2.137H6.111v2.137zm.259-4.852l10.48 2.189.451-2.07-10.478-2.187-.453 2.068zm1.359-5.056l9.705 4.53.903-1.95-9.706-4.53-.902 1.936v.014zm2.715-4.785l8.217 6.855 1.359-1.62-8.216-6.853-1.35 1.617-.01.001zM15.751 0l-1.746 1.294 6.405 8.604 1.746-1.294L15.749 0h.002z" />
            </svg>
          </a>
          <a href="https://www.getrevue.co/profile/dagster">
            <svg
              className="h-7 w-7 text-gray-400 hover:text-blue-500 transition transform hover:scale-105 hover:rotate-6"
              role="img"
              viewBox="0 0 20 20"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"></path>
              <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"></path>
            </svg>
          </a>
          <button
            onClick={() => setDarkMode(!isDarkMode)}
            type="button"
            className={cx(
              "relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500",
              {
                "bg-gray-800": isDarkMode,
                "bg-gray-200": !isDarkMode,
              }
            )}
            aria-pressed="false"
          >
            <span className="sr-only">Use setting</span>
            {/* Enabled: "translate-x-5", Not Enabled: "translate-x-0" */}
            <span
              className={cx(
                "pointer-events-none relative inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200",
                {
                  "translate-x-5": isDarkMode,
                  "translate-x-0": !isDarkMode,
                }
              )}
            >
              {/* Enabled: "opacity-0 ease-out duration-100", Not Enabled: "opacity-100 ease-in duration-200" */}
              <span
                className={cx(
                  "absolute inset-0 h-full w-full flex items-center justify-center transition-opacity",
                  {
                    "opacity-0 ease-out duration-100": isDarkMode,
                    "opacity-100 ease-in duration-200": !isDarkMode,
                  }
                )}
                aria-hidden="true"
              >
                <svg
                  className="bg-white h-3 w-3 text-gray-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"
                    clipRule="evenodd"
                  ></path>
                </svg>
              </span>
              {/* Enabled: "opacity-100 ease-in duration-200", Not Enabled: "opacity-0 ease-out duration-100" */}
              <span
                className={cx(
                  "absolute inset-0 h-full w-full flex items-center justify-center transition-opacity",
                  {
                    "opacity-100 ease-in duration-200": isDarkMode,
                    "opacity-0 ease-out duration-100": !isDarkMode,
                  }
                )}
                aria-hidden="true"
              >
                <svg
                  className="bg-white h-3 w-3 text-indigo-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"></path>
                </svg>
              </span>
            </span>
          </button>
        </div>
        {/* End secondary column */}
      </div>
    </div>
  );
};

const Layout = ({ children }) => {
  const [isFeedbackOpen, setOpenFeedback] = useState<boolean>(false);
  const [isMobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const [isDarkMode, setDarkMode] = useLocalStorage<boolean>(
    "dagster.dark",
    false
  );

  const closeFeedback = () => {
    setOpenFeedback(false);
  };

  const toggleFeedback = () => {
    setOpenFeedback(!isFeedbackOpen);
  };

  const openMobileMenu = () => {
    setMobileMenuOpen(true);
  };

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  return (
    <>
      <Sidebar
        isMobileMenuOpen={isMobileMenuOpen}
        closeMobileMenu={closeMobileMenu}
      />
      <div
        className={cx("flex transition-colors", {
          "dark bg-gray-900": isDarkMode,
          "bg-white": !isDarkMode,
        })}
      >
        <FeedbackModal isOpen={isFeedbackOpen} closeFeedback={closeFeedback} />
        {/* Placeholder spacer for navbar */}
        <div className="relative hidden lg:flex lg:flex-shrink-0">
          <div className="flex flex-col w-80 border-r border-gray-200 dark:border-gray-700 pt-4 pb-4 bg-gray-100 dark:bg-gray-900"></div>
        </div>
        {/* End placeholder spacer for navbar */}
        <div className="w-full overflow-y-scroll">
          <div className="max-w-7xl mx-auto">
            <div className="relative w-full">
              <div className="lg:hidden">
                <div className="flex items-center justify-between bg-gray-50 border-b border-gray-200 px-4 py-1.5">
                  <div className="flex items-center">
                    <img
                      className="w-32 inline-block"
                      src="/assets/logos/dagster-logo.svg"
                    />
                  </div>
                  
                  <div>
                    <button
                      onClick={openMobileMenu}
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
              <Header
                openFeedback={toggleFeedback}
                isDarkMode={isDarkMode}
                setDarkMode={setDarkMode}
              />

              <div className="w-full relative z-0 flex justify-center mb-8">
                {children}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export const getLayout = (page) => <Layout>{page}</Layout>;

export default Layout;
