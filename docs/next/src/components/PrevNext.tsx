import { useRouter } from 'next/router';
import Link from 'next/link';
import { flatten } from 'utils/treeOfContents/flatten';
import { useTreeOfContents } from 'hooks/useTreeOfContents';

export const PrevNext = () => {
  const treeOfContents = useTreeOfContents();
  const router = useRouter();

  const allLinks = flatten(Object.values(treeOfContents), true)
    .filter(({ isExternal }) => !isExternal)
    .filter(({ ignore }) => !ignore);

  const selectedItems = allLinks.filter((l) => router.asPath.includes(l.path));
  const selectedItem = selectedItems[selectedItems.length - 1];
  const currentIndex = allLinks.indexOf(selectedItem);

  let prev = 0;
  let next = 0;

  if (currentIndex === 0) {
    prev = allLinks.length - 1;
    next = currentIndex + 1;
  } else if (currentIndex === allLinks.length - 1) {
    prev = currentIndex - 1;
    next = 0;
  } else {
    prev = currentIndex - 1;
    next = currentIndex + 1;
  }

  return (
    <div className="flex flex-row justify-between">
      {allLinks[prev] && (
        <span className="mr-2 ml-1 rounded-md shadow-sm block">
          <Link href={allLinks[prev].path} passHref>
            <a className="inline-flex items-center px-4 py-2 border border-blue-300 text-base leading-6 font-medium rounded-md text-gray-700 bg-white hover:text-gray-500 focus:outline-none focus:border-blue-300 focus:shadow-outline-blue active:text-gray-800 active:bg-gray-50 transition ease-in-out duration-150">
              <svg
                className="mr-5 md:mr-0 h-5 w-5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
              {allLinks[prev].name}
            </a>
          </Link>
        </span>
      )}
      <span className="ml-2 mr-1 rounded-md shadow-sm block">
        <Link href={allLinks[next].path} passHref>
          <a className="inline-flex items-center px-4 py-2 border border-blue-300 text-base leading-6 font-medium rounded-md text-gray-700 bg-white hover:text-gray-500 focus:outline-none focus:border-blue-300 focus:shadow-outline-blue active:text-gray-800 active:bg-gray-50 transition ease-in-out duration-150">
            {allLinks[next].name}
            <svg
              className="ml-5 md:ml-0 h-5 w-5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                clipRule="evenodd"
              />
            </svg>
          </a>
        </Link>
      </span>
    </div>
  );
};
