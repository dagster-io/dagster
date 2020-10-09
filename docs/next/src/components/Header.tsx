import CommunityLinks from './CommunityLinks';
import { VersionedLink, VersionedImage } from './VersionedComponents';
import Search from './Search';
import DocSearch from './Docsearch';
import React, { useState } from 'react';
import cx from 'classnames';
import getConfig from 'next/config';
import { useRouter } from 'next/router';

type HeaderProps = {
  onMobileToggleSidebarClick: () => void;
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

const Header: React.FC<HeaderProps> = ({ onMobileToggleSidebarClick }) => {
  const [isMobileHeaderOpen, setIsMobileHeaderOpen] = useState(false);
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
    <nav className="bg-white shadow-sm lg:fixed lg:left-0 lg:right-0 lg:h-16 lg:z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center lg:hidden">
            <button
              onClick={() => onMobileToggleSidebarClick()}
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
                  d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
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
          <div className="flex">
            <a
              href="https://dagster.io"
              className="flex-shrink-0 flex items-center"
            >
              <img
                className="block h-6 w-auto"
                src="/assets/logos/small.png"
                alt="Dagster logo"
              />
              <div
                className="text-lg font-bold tracking-widest uppercase hidden md:block"
                style={{ marginLeft: '.75rem' }}
              >
                Dagster
              </div>
            </a>
            <div className="hidden sm:ml-6 sm:flex">
              <a
                href="https://dagster.io"
                className="ml-8 inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium leading-5 text-gray-500 hover:text-gray-700 hover:border-gray-300 focus:outline-none focus:text-gray-700 focus:border-gray-300 transition duration-150 ease-in-out"
              >
                Home
              </a>
              <a
                href="https://dagster.io/blog"
                className="ml-8 inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium leading-5 text-gray-500 hover:text-gray-700 hover:border-gray-300 focus:outline-none focus:text-gray-700 focus:border-gray-300 transition duration-150 ease-in-out"
              >
                Blog
              </a>
              <VersionedLink href="/">
                <a
                  className={cx(
                    'ml-8 inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium leading-5 text-gray-500 focus:outline-none focus:border-indigo-700 transition duration-150 ease-in-out',
                    {
                      'border-indigo-500 text-gray-900 ': !router.pathname.startsWith(
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
                    'ml-8 inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium leading-5 text-gray-500 focus:outline-none focus:border-indigo-700 transition duration-150 ease-in-out',
                    {
                      'border-indigo-500 text-gray-900 ': router.pathname.startsWith(
                        '/_apidocs',
                      ),
                    },
                  )}
                >
                  API Docs
                </a>
              </VersionedLink>
            </div>
          </div>
          {isApiDocs ? <Search /> : <DocSearch />}

          <div className="flex-shrink-0 flex items-center">
            <div className="group ml-3 relative tracking-wide border-b font-medium cursor-pointer">
              <a href="/versions">{version}</a>
            </div>
          </div>

          <div className="hidden lg:ml-4 lg:flex lg:items-center">
            <CommunityLinks className="w-40" />
          </div>

          <div className="-mr-2 flex items-center sm:hidden">
            {/* Mobile menu button */}
            <button
              onClick={() => {
                setIsMobileHeaderOpen(!isMobileHeaderOpen);
              }}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:bg-gray-100 focus:text-gray-500 transition duration-150 ease-in-out"
            >
              {/* Menu open: "hidden", Menu closed: "block" */}
              <svg
                className="block h-6 w-6"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
              {/* Menu open: "block", Menu closed: "hidden" */}
              <svg
                className="hidden h-6 w-6"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 24 24"
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

        <div className={`${isMobileHeaderOpen ? 'block' : 'hidden'} sm:hidden`}>
          <div className="pt-2 pb-3">
            <a
              href="https://dagster.io"
              className="block block pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-50 hover:border-gray-300 focus:outline-none focus:text-gray-800 focus:bg-gray-50 focus:border-gray-300 transition duration-150 ease-in-out"
            >
              Home
            </a>
            <a
              href="https://dagster.io/blog"
              className="mt-1 block pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-50 hover:border-gray-300 focus:outline-none focus:text-gray-800 focus:bg-gray-50 focus:border-gray-300 transition duration-150 ease-in-out"
            >
              Blog
            </a>
            <VersionedLink href="/install">
              <a
                className={cx(
                  'mt-1 block pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-50 hover:border-gray-300 focus:outline-none focus:text-gray-800 focus:bg-gray-50 focus:border-gray-300 transition duration-150 ease-in-out',
                  {
                    'text-indigo-700 bg-indigo-50 hover:text-indigo-700 hover:bg-indigo-50 focus:border-indigo-700 focus:bg-indigo-100 focus:text-indigo-800': !router.pathname.startsWith(
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
                  'mt-1 block pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-50 hover:border-gray-300 focus:outline-none focus:text-gray-800 focus:bg-gray-50 focus:border-gray-300 transition duration-150 ease-in-out',
                  {
                    'text-indigo-700 bg-indigo-50 hover:text-indigo-700 hover:bg-indigo-50 focus:border-indigo-700 focus:bg-indigo-100 focus:text-indigo-800': router.pathname.startsWith(
                      '/_apidocs',
                    ),
                  },
                )}
                // className="mt-1 block pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-50 hover:border-gray-300 focus:outline-none focus:text-gray-800 focus:bg-gray-50 focus:border-gray-300 transition duration-150 ease-in-out"
              >
                API Docs
              </a>
            </VersionedLink>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Header;
