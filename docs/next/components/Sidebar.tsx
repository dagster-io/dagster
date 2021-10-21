import { Menu, Transition } from "@headlessui/react";

import Icons from "../components/Icons";
import Link from "./Link";
import cx from "classnames";
import { useNavigation } from "../util/useNavigation";
import { useVersion } from "../util/useVersion";

const getCurrentSection = (navigation) => {
  const { asPath } = useVersion();
  const match = navigation.find(
    (item) => item.path !== "/" && asPath.startsWith(item.path)
  );
  return match || navigation.find((item) => item.path === "/");
};

const TopLevelNavigation = () => {
  const navigation = useNavigation();
  const currentSection = getCurrentSection(navigation);

  return (
    <div className="space-y-1">
      {navigation.map((item) => {
        const match = item == currentSection;

        return (
          <Link key={item.path} href={item.path}>
            <a
              className={cx(
                "group flex items-center px-2 py-2 text-sm font-medium rounded-md text-gray-900 dark:text-gray-200",
                {
                  "bg-gray-200 dark:bg-gray-600": match,
                  "hover:text-gray-900 hover:bg-gray-50 dark:hover:text-gray-300 dark:hover:bg-gray-700": !match,
                }
              )}
            >
              <svg
                className="mr-3 h-6 w-6 text-gray-400 group-hover:text-gray-500"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                {Icons[item.icon]}
              </svg>
              <span className={cx({ "DocSearch-lvl0": match })}>
                {item.title}
              </span>
            </a>
          </Link>
        );
      })}
    </div>
  );
};

const SecondaryNavigation = () => {
  const navigation = useNavigation();
  const currentSection = getCurrentSection(navigation);
  const { asPathWithoutAnchor } = useVersion();

  if (!currentSection?.children) {
    return null;
  }

  return (
    <>
      {currentSection.children.map((section) => {
        const match = section.children.find(
          (section) => section.path == asPathWithoutAnchor
        );

        return (
          <div key={section.title} className="mt-8">
            <h3
              className={cx(
                "px-3 text-xs font-semibold text-blue-500 dark:text-blue-200 uppercase tracking-wider",
                {
                  "DocSearch-lvl1": match,
                }
              )}
              id="teams-headline"
            >
              {section.title}
            </h3>

            <div className="border-l-2 ml-3 mt-4">
              <div
                className="mt-1 ml-1 space-y-1"
                role="group"
                aria-labelledby="teams-headline"
              >
                {section.children.map((section) => {
                  return (
                    <ThirdLevelNavigation
                      key={section.title}
                      section={section}
                    />
                  );
                })}
              </div>
            </div>
          </div>
        );
      })}
    </>
  );
};

const ThirdLevelNavigation = ({ section }) => {
  const { asPathWithoutAnchor } = useVersion();

  return (
    <Link href={section.path}>
      <a
        className={cx(
          "group flex items-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 rounded-md hover:text-gray-900 hover:bg-gray-50 dark:hover:bg-gray-700",
          {
            "bg-blue-100 text-gray-900 hover:bg-blue-100 dark:bg-gray-600":
              section.path === asPathWithoutAnchor,
          }
        )}
      >
        <span
          className={cx({
            "DocSearch-lvl2": section.path === asPathWithoutAnchor,
          })}
        >
          {section.title}
        </span>
      </a>
    </Link>
  );
};

const VersionDropdown = () => {
  const {
    latestVersion,
    version: currentVersion,
    versions,
    asPath,
  } = useVersion();

  return (
    <div className="z-20 px-3 relative inline-block text-left">
      <div className="relative block text-left">
        <Menu>
          {({ open }) => (
            <>
              <div>
                <Menu.Button className="group w-full bg-gray-50 dark:bg-gray-800 rounded-md px-3.5 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:border-gray-200 border-2 dark:border-gray-700">
                  <span className="flex w-full justify-between items-center">
                    <span className="flex min-w-0 items-center justify-between space-x-3">
                      <span className="flex-1 min-w-0">
                        <span className="text-gray-900 text-sm font-medium truncate"></span>{" "}
                        <span className="text-gray-500 dark:text-gray-300 text-sm truncate">
                          {currentVersion}{" "}
                          {currentVersion === latestVersion && "(latest)"}
                        </span>
                      </span>
                    </span>
                    {/* Heroicon name: selector */}
                    <svg
                      className="flex-shrink-0 h-5 w-5 text-gray-400 group-hover:text-gray-500"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 3a1 1 0 01.707.293l3 3a1 1 0 01-1.414 1.414L10 5.414 7.707 7.707a1 1 0 01-1.414-1.414l3-3A1 1 0 0110 3zm-3.707 9.293a1 1 0 011.414 0L10 14.586l2.293-2.293a1 1 0 011.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                        clipRule="evenodd"
                      />
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
                  className="absolute mx-3 right-0 left-0 mt-2 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 divide-y divide-gray-200 overflow-y-scroll max-h-(screen-60)"
                >
                  <div className="px-4 py-3">
                    <p className="text-sm leading-5">
                      You are currently viewing the docs for Dagster{" "}
                      <span className="text-sm font-medium leading-5 text-gray-900">
                        {currentVersion}
                      </span>
                      . You can select a different version below.
                    </p>
                  </div>

                  <div className="py-1">
                    {versions.map((version) => {
                      return (
                        <Link key={asPath} href={asPath} version={version}>
                          <Menu.Item>
                            {({ active }) => (
                              <a
                                className={`${
                                  active
                                    ? "bg-gray-100 text-gray-900"
                                    : "text-gray-700"
                                } flex cursor-pointer justify-between w-full px-4 py-2 text-sm leading-5 text-left`}
                              >
                                {version}
                              </a>
                            )}
                          </Menu.Item>
                        </Link>
                      );
                    })}
                  </div>

                  <div className="py-1">
                    <Menu.Item>
                      {({ active }) => (
                        <a
                          href="https://legacy-docs.dagster.io"
                          className={`${
                            active
                              ? "bg-gray-100 text-gray-900"
                              : "text-gray-700"
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
};

const SidebarContents = () => {
  return (
    <>
      <div className="flex items-center flex-shrink-0 px-6 pt-2 pb-4">
        <a href="/" className="flex items-center">
          <img
            className="w-5 h-5 inline-block"
            src="https://docs.dagster.io/assets/logos/small.png"
          />
          <span className="ml-2 text-lg font-extrabold dark:text-gray-200">
            Dagster
          </span>
          <span className="ml-1 text-lg font-extrabold text-gray-700 dark:text-gray-200">
            Docs
          </span>
        </a>
      </div>
      <VersionDropdown />
      {/* Sidebar component, swap this element with another sidebar if you like */}
      <div className="h-0 flex-1 flex flex-col overflow-y-auto">
        <div className="hidden lg:block h-6 pointer-events-none absolute inset-x-0 right-1 z-10 bg-gradient-to-b from-gray-100 dark:from-gray-900"></div>
        {/* Sidebar Search */}
        <div className="hidden px-3 mt-5">
          <label htmlFor="search" className="sr-only">
            Search
          </label>
          <div className="mt-1 relative rounded-md shadow-sm">
            <div
              className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"
              aria-hidden="true"
            >
              {/* Heroicon name: search */}
              <svg
                className="mr-3 h-4 w-4 text-gray-400"
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
              type="text"
              name="search"
              id="search"
              className="focus:ring-indigo-500 focus:border-indigo-500 block w-full pl-9 sm:text-sm border-gray-300 rounded-md"
              placeholder="Search"
            />
          </div>
        </div>
        {/* Navigation */}
        <nav className="px-3 mt-6">
          <TopLevelNavigation />
          <div className="mt-8">
            <SecondaryNavigation />
          </div>
        </nav>
      </div>
    </>
  );
};

const Sidebar = ({ isMobileMenuOpen, closeMobileMenu }) => {
  return (
    <>
      {/* Off-canvas menu for mobile, show/hide based on off-canvas menu state. */}
      <Transition show={isMobileMenuOpen}>
        <div className="lg:hidden">
          <div className="fixed inset-0 flex z-40">
            <Transition.Child
              enter="transition-opacity ease-in-out duration-300"
              enterFrom="opacity-0"
              enterTo="opacity-100"
              leave="transition-opacity ease-in-out duration-300"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <div className="fixed inset-0" aria-hidden="true">
                <div className="absolute inset-0 bg-gray-600 opacity-75" />
              </div>
            </Transition.Child>
            <Transition.Child
              enter="transition ease-in-out duration-300 transform"
              enterFrom="-translate-x-full"
              enterTo="translate-x-0"
              leave="transition ease-in-out duration-300 transform"
              leaveFrom="translate-x-0"
              leaveTo="-translate-x-full"
            >
              <div className="relative flex-1 flex flex-col w-96 max-w-xs  pt-5 pb-4 bg-white h-full">
                <Transition.Child
                  enter="transition-opacity duration-100"
                  enterFrom="opacity-0"
                  enterTo="opacity-100"
                  leave="transition-opacity duration-150"
                  leaveFrom="opacity-100"
                  leaveTo="opacity-0"
                >
                  <div className="absolute top-0 right-0 -mr-12 pt-2">
                    <button
                      onClick={closeMobileMenu}
                      className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                    >
                      <span className="sr-only">Close sidebar</span>
                      {/* Heroicon name: x */}
                      <svg
                        className="h-6 w-6 text-white"
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
                </Transition.Child>

                <SidebarContents />
              </div>
            </Transition.Child>

            <div className="flex-shrink-0 w-14" aria-hidden="true">
              {/* Dummy element to force sidebar to shrink to fit close icon */}
            </div>
          </div>
        </div>
      </Transition>

      {/* Static sidebar for desktop */}
      <div className="hidden z-50 lg:block fixed top-0 bottom-0 lg:flex-shrink-0">
        <div className="h-full flex flex-col w-80 border-r border-gray-200 dark:border-gray-700 pt-4 pb-4 bg-gray-100 dark:bg-gray-900">
          <SidebarContents />
        </div>
      </div>
    </>
  );
};

export default Sidebar;
