import { flatten, useNavigation } from "util/useNavigation";

import Link from "./Link";
import React from "react";
import { useVersion } from "../util/useVersion";

const Pagination = () => {
  const { asPath } = useVersion();
  const navigation = useNavigation();
  const flattenedNavigation = flatten(navigation).filter(
    (n: { path: any }) => n.path
  );

  const currentIndex = flattenedNavigation.findIndex(
    (n: { path: string }) => n.path === asPath
  );
  const prev = flattenedNavigation[currentIndex - 1];
  const next = flattenedNavigation[currentIndex + 1];

  return (
    <nav className="mt-12 mb-12 border-t border-gray-200 px-4 flex items-center justify-between sm:px-0">
      <div className="w-0 flex-1 flex">
        {prev && (
          <Link href={prev.path}>
            <a className="border-t-2 border-transparent pt-4 pr-1 inline-flex items-center text-sm md:text-base font-medium text-gray-500 dark:text-gray-200 hover:text-gray-700 hover:border-gray-300">
              {/* Heroicon name: arrow-narrow-left */}
              <svg
                className="mr-3 h-5 w-5 text-gray-400"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M7.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l2.293 2.293a1 1 0 010 1.414z"
                  clipRule="evenodd"
                />
              </svg>
              {prev.title}
            </a>
          </Link>
        )}
      </div>
      <div className="w-0 flex-1 flex justify-end">
        {next && (
          <Link href={next.path}>
            <a className="border-t-2 border-transparent pt-4 pl-1 inline-flex items-center text-sm md:text-base font-medium text-gray-500 dark:text-gray-200 hover:text-gray-700 hover:border-gray-300">
              {next.title}
              {/* Heroicon name: arrow-narrow-right */}
              <svg
                className="ml-3 h-5 w-5 text-gray-400"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </a>
          </Link>
        )}
      </div>
    </nav>
  );
};

export default Pagination;
