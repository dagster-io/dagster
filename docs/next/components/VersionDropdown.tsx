import {Menu, Transition} from '@headlessui/react';
import React from 'react';

import Icons from '../components/Icons';
import {useVersion} from '../util/useVersion';

import Link from './Link';

function getLibraryVersion(coreVersion) {
  const [major, minor, patch] = coreVersion.split('.');
  return parseInt(major) < 1 ? coreVersion : ['0', 16 + parseInt(minor), patch].join('.');
}

function getLibraryVersionText(coreVersion) {
  const libraryVersion = coreVersion === 'master' ? 'master' : getLibraryVersion(coreVersion);
  return libraryVersion === 'master' || coreVersion === libraryVersion
    ? ''
    : `/ ${libraryVersion} (libs)`;
}

export default function VersionDropdown() {
  const {version: currentVersion, versions, asPath} = useVersion();
  const libraryVersionText = getLibraryVersionText(currentVersion);
  return (
    <div className="z-20 relative inline-flex text-left w-full">
      <div className="relative block text-left w-full">
        <Menu>
          {({open}) => (
            <>
              <div>
                <Menu.Button className="group rounded-full px-2 lg:px-4 lg:py-2 text-gray-400 border border-gray-300 hover:bg-white transition-colors duration-200">
                  <span className="flex w-full justify-between items-center gap-x-2">
                    <span className="flex min-w-0 items-center justify-between space-x-3">
                      <span className="flex-1 min-w-0 text-gable-green dark:text-gray-300 text-xs lg:text-sm truncate space-x-1">
                        <span>
                          {currentVersion} {libraryVersionText}
                        </span>
                      </span>
                    </span>
                    {/* Heroicon name: selector */}
                    <svg
                      className="h-2 w-2 lg:h-3 lg:w-3"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 20 20"
                      stroke="currentColor"
                      aria-hidden="true"
                    >
                      {Icons['ChevronDown']}
                    </svg>
                  </span>
                </Menu.Button>
              </div>

              <Transition
                show={open}
                enter="transition ease-out duration-100"
                enterFrom="transform opacity-0 scale-95"
                enterTo="transform opacity-100 scale-100"
                leave="transition ease-in duration-75"
                leaveFrom="transform opacity-100 scale-100"
                leaveTo="transform opacity-0 scale-95"
              >
                <Menu.Items
                  static
                  className="absolute w-full lg:w-60 lg:mx-3 right-0 left-0 mt-2 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 divide-y divide-gray-200 overflow-y-scroll max-h-(screen-60)"
                >
                  <div className="px-4 py-3">
                    <p className="text-sm leading-5">
                      You&apos;re currently viewing the docs for Dagster{' '}
                      <span className="text-sm font-medium leading-5 text-gray-900">
                        {currentVersion}
                      </span>
                      . Select a different version below. Note that prior to 1.0, all Dagster
                      packages shared the same version. After 1.0, we adopted separate version
                      tracks to differentiate less mature integration libraries.{' '}
                      <Link href="/getting-started/releases#dagster-integration-libraries">
                        <span className="hover:underline cursor-pointer">Learn more</span>
                      </Link>
                      .
                    </p>
                  </div>

                  <div className="py-1">
                    {versions.map((version) => {
                      const libraryVersionText = getLibraryVersionText(version);
                      return (
                        <Link key={version} href={asPath} version={version}>
                          <Menu.Item>
                            {({active}) => (
                              <a
                                className={`${
                                  active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                                } flex cursor-pointer justify-between w-full px-4 py-2 text-sm leading-5 text-left`}
                              >
                                {version} {libraryVersionText}
                              </a>
                            )}
                          </Menu.Item>
                        </Link>
                      );
                    })}
                  </div>

                  <div className="py-1">
                    <Menu.Item>
                      {({active}) => (
                        <a
                          href="https://legacy-docs.dagster.io"
                          className={`${
                            active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                          } flex justify-between w-full px-4 py-2 text-sm leading-5 text-left`}
                        >
                          Legacy Site (pre-0.11.0)
                        </a>
                      )}
                    </Menu.Item>
                  </div>
                </Menu.Items>
              </Transition>
            </>
          )}
        </Menu>
      </div>
    </div>
  );
}
