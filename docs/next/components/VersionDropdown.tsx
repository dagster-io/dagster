import { useVersion } from "../util/useVersion";
import { Menu, Transition } from "@headlessui/react";
import Link from "./Link";

export function VersionDropdown() {
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
}
