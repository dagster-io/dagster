import cx from 'classnames';
import NextLink from 'next/link';
import {useRouter} from 'next/router';

/**
 * `currentPageIndex` is zero-indexed
 */
export function PagePagination(props: {currentPageIndex: number; totalPageCount: number}) {
  const {currentPageIndex, totalPageCount} = props;
  const {query} = useRouter();

  const separator = (
    <span className="inline-flex items-center border-t-2 border-transparent px-4 pt-4 text-sm font-medium text-gray-500">
      ...
    </span>
  );

  const indexList = Array.from({length: totalPageCount}, (_, i) => i);
  let content: React.ReactNode;

  if (totalPageCount <= 7) {
    // 1 / 2 / 3 / 4 / 5 / 6 / 7
    // ^   ^   ^   ^   ^   ^   ^ (current page can be here)
    content = (
      <>
        {indexList.map((i) => (
          <PaginationItem key={i} targetIndex={i} isCurrentPage={currentPageIndex === i} />
        ))}
      </>
    );
  } else if (currentPageIndex < 2 || currentPageIndex >= totalPageCount - 2) {
    // 1 / 2 / 3 ... 8 / 9 / 10
    // ^   ^             ^   ^  (current page can be here)
    content = (
      <>
        {indexList.slice(0, 3).map((i) => (
          <PaginationItem
            key={`before-${i}`}
            targetIndex={i}
            isCurrentPage={currentPageIndex === i}
          />
        ))}
        {separator}
        {indexList.slice(-3).map((i) => (
          <PaginationItem
            key={`after-${i}`}
            targetIndex={i}
            isCurrentPage={currentPageIndex === i}
          />
        ))}
      </>
    );
  } else if (currentPageIndex === 2 || currentPageIndex === totalPageCount - 3) {
    // 1 / 2 / 3 / 4 ... 28
    //         ^               (current page can be here)
    // 1 ... 25 / 26 / 27 / 28
    //            ^            (current page can be here)
    const leftCount = currentPageIndex === 2 ? 4 : 1;
    const rightCount = currentPageIndex === totalPageCount - 3 ? 4 : 1;

    content = (
      <>
        {indexList.slice(0, leftCount).map((i) => (
          <PaginationItem
            key={`before-${i}`}
            targetIndex={i}
            isCurrentPage={currentPageIndex === i}
          />
        ))}
        {separator}
        {indexList.slice(-rightCount).map((i) => (
          <PaginationItem
            key={`after-${i}`}
            targetIndex={i}
            isCurrentPage={currentPageIndex === i}
          />
        ))}
      </>
    );
  } else {
    // 1 ... 3 / 4 / 5 ... 28
    //           ^               (current page can be here)
    content = (
      <>
        <PaginationItem targetIndex={0} isCurrentPage={false} />
        {separator}
        {[currentPageIndex - 1, currentPageIndex, currentPageIndex + 1].map((i) => (
          <PaginationItem key={i} targetIndex={i} isCurrentPage={currentPageIndex === i} />
        ))}
        {separator}
        <PaginationItem targetIndex={totalPageCount - 1} isCurrentPage={false} />
      </>
    );
  }

  return (
    <nav className="flex items-center justify-between border-t border-gray-200 px-4 sm:px-0 mt-16">
      <div className="-mt-px flex w-0 flex-1">
        {currentPageIndex === 0 ? null : (
          <NextLink
            legacyBehavior
            href={{
              query: {...query, page: currentPageIndex},
            }}
          >
            <a className="inline-flex items-center border-t-2 border-transparent pr-1 pt-4 text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700">
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
              Previous
            </a>
          </NextLink>
        )}
      </div>
      <div className="hidden md:-mt-px md:flex">{content}</div>
      <div className="sm:flex md:hidden">
        <span className="inline-flex items-center border-t-2 border-transparent px-4 pt-4 text-sm font-medium text-gray-500">
          Page {currentPageIndex + 1} of {totalPageCount}
        </span>
      </div>
      <div className="-mt-px flex w-0 flex-1 justify-end">
        {currentPageIndex === totalPageCount - 1 ? null : (
          <NextLink
            legacyBehavior
            href={{
              query: {...query, page: currentPageIndex + 2},
            }}
          >
            <a className="inline-flex items-center border-t-2 border-transparent pl-1 pt-4 text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700">
              Next
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
          </NextLink>
        )}
      </div>
    </nav>
  );
}

/**
 * `targetIndex` is zero-indexed
 */
function PaginationItem(props: {targetIndex: number; isCurrentPage?: boolean}) {
  const {targetIndex, isCurrentPage = false} = props;
  const {query} = useRouter();

  return (
    <NextLink
      legacyBehavior
      href={{
        query: {...query, page: targetIndex + 1},
      }}
    >
      <a
        className={cx({
          'inline-flex items-center border-t-2 border-transparent px-4 pt-4 text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700':
            true,
          'border-indigo-500 text-indigo-600': isCurrentPage,
        })}
      >
        {targetIndex + 1}
      </a>
    </NextLink>
  );
}
