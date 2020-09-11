import CommunityLinks from './CommunityLinks';
import { VersionedLink, VersionedImage } from './VersionedComponents';
import Search from './Search';
import DocSearch from './Docsearch';
import React, { useState } from 'react';
import cx from 'classnames';
import getConfig from 'next/config';
import { useRouter } from 'next/router';

type HeaderProps = {
  onMobileToggleNavigationClick: () => void;
};

const Version: React.FC<{ name: string }> = ({ name }) => {
  return (
    <a
      href={`/${name}`}
      className="block px-4 py-2 text-sm leading-5 text-gray-700 hover:bg-gray-100 focus:outline-none focus:bg-gray-100 transition duration-150 ease-in-out"
    >
      {name}
    </a>
  );
};

const Header: React.FC<HeaderProps> = ({ onMobileToggleNavigationClick }) => {
  const config = getConfig();

  let version = 'latest';
  if (config) {
    const { publicRuntimeConfig } = getConfig();
    if (publicRuntimeConfig.version) {
      version = publicRuntimeConfig.version;
    }
  }

  const router = useRouter();

  const isApiDocs = router.pathname.startsWith('/_apidocs');

  return (
    <nav className="bg-white border-b border-gray-200 shadow fixed left-0 right-0 h-16 z-10">
      <div className="mx-auto px-2 sm:px-4 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex px-2 lg:px-0">
            <div className="flex-shrink-0 flex items-center">
              <VersionedLink href="/">
                <a>
                  <VersionedImage
                    className="block h-6 w-auto"
                    src="/assets/logos/small.png"
                    alt="Logo"
                  />
                </a>
              </VersionedLink>
              <div className="ml-3 flex items-baseline">
                <VersionedLink href="/">
                  <a>
                    <div className="text-lg font-bold tracking-widest uppercase hidden md:block">
                      Dagster
                    </div>
                  </a>
                </VersionedLink>

                <div className="group ml-3 relative tracking-wide border-b font-medium cursor-pointer">
                  <a href="/versions">{version}</a>
                </div>
              </div>
            </div>
            <div className="ml-6 flex">
              <VersionedLink href="/install">
                <a
                  className={cx(
                    'inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium leading-5 text-gray-900 focus:outline-none focus:border-indigo-700 transition duration-150 ease-in-out',
                    {
                      'border-indigo-500': !router.pathname.startsWith(
                        '/_apidocs',
                      ),
                    },
                  )}
                >
                  Docs
                </a>
              </VersionedLink>

              <VersionedLink href="/_apidocs">
                <a
                  className={cx(
                    'ml-2 lg:ml-8 inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium leading-5 text-gray-500 focus:outline-none focus:border-indigo-700 transition duration-150 ease-in-out',
                    {
                      'border-indigo-500': router.pathname.startsWith(
                        '/_apidocs',
                      ),
                    },
                  )}
                >
                  API Docs
                </a>
              </VersionedLink>

              <a
                href="https://dagster.io/blog"
                target="_blank"
                className="ml-2 lg:ml-8 inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium leading-5 text-gray-500 hover:text-gray-700 hover:border-gray-300 focus:outline-none focus:text-gray-700 focus:border-gray-300 transition duration-150 ease-in-out"
              >
                Blog
              </a>
            </div>
          </div>
          {isApiDocs ? <Search /> : <DocSearch />}
          <div className="flex items-center lg:hidden">
            <button
              onClick={() => onMobileToggleNavigationClick()}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:bg-gray-100 focus:text-gray-500 transition duration-150 ease-in-out"
            >
              {/* <!-- Icon when menu is closed. -->
          <!-- Menu open: "hidden", Menu closed: "block" --> */}
              <svg
                className="block h-6 w-6"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
              {/* <!-- Icon when menu is open. -->
          <!-- Menu open: "block", Menu closed: "hidden" --> */}
              <svg
                className="hidden h-6 w-6"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <div className="hidden lg:ml-4 lg:flex lg:items-center">
            <CommunityLinks className="w-40" />
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Header;
