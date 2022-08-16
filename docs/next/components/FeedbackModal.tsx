import {Transition} from '@headlessui/react';
import newGithubIssueUrl from 'new-github-issue-url';
import React, {useEffect, useState} from 'react';

import {useVersion} from '../util/useVersion';

const FeedbackModal = ({isOpen, closeFeedback}: {isOpen: boolean; closeFeedback: () => void}) => {
  const {asPath, version} = useVersion();
  const [currentPage, setCurrentPage] = useState<string>(asPath);
  const [currentVersion, setCurrentVersion] = useState<string>(version);
  const [description, setDescription] = useState<string>('');
  const [title, setTitle] = useState<string>('');
  const [submitOption, setSubmitOption] = useState<string>('GH');

  const enablePrivateSubmition = false;

  useEffect(() => {
    setCurrentVersion(version);
    setCurrentPage(asPath);
    setTitle(`Problem on ${asPath} page`);
  }, [asPath, version]);

  const submitFeedback = (e) => {
    e.preventDefault();

    const url = newGithubIssueUrl({
      user: 'dagster-io',
      repo: 'dagster',
      title: `[Documentation Feedback] ${title}`,
      body: description,
      labels: ['documentation'],
    });

    window.open(url, '_blank');
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
                    <h2 id="slide-over-heading" className="text-lg font-medium text-white">
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
                      Feedback helps us improve our documentation so you can be more productive.
                      Please let us know about anything!
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
                            onChange={(event) => setCurrentPage(event.target.value)}
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
                            onChange={(event) => setCurrentVersion(event.target.value)}
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
                            defaultValue=""
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                          />
                        </div>
                      </div>

                      {enablePrivateSubmition && (
                        <>
                          <fieldset>
                            <legend className="sr-only">Submit as Public Github Issue</legend>
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
                                    checked={submitOption === 'GH'}
                                    onChange={(e) => setSubmitOption(e.target.value)}
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
                                    Submit this feedback to our public issue tracker at{' '}
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
                                    checked={submitOption === 'Private'}
                                    onChange={(e) => setSubmitOption(e.target.value)}
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

                          {submitOption === 'Private' && (
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

export default FeedbackModal;
