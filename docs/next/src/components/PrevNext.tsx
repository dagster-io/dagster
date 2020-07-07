import { useRouter } from 'next/router';
import { flatten, TreeLink } from 'utils/treeOfContents/flatten';
import { useTreeOfContents } from 'hooks/useTreeOfContents';
import { VersionedLink } from './VersionedComponents';

export const PrevNext = () => {
  const treeOfContents = useTreeOfContents();
  const router = useRouter();

  const allLinks = treeOfContents
    // Flatten links within each section
    .map((val) =>
      flatten([val], true)
        .filter(({ isExternal }) => !isExternal)
        .filter(({ ignore }) => !ignore),
    )
    // Only keep top-level section which contains the current path
    .find((section) => section.some((t) => router.asPath.includes(t.path)));

  if (!allLinks || allLinks.length === 0) {
    return <nav></nav>;
  }

  const selectedItems = allLinks.filter((l) => router.asPath.includes(l.path));
  const selectedItem = selectedItems[selectedItems.length - 1];
  const currentIndex = allLinks.indexOf(selectedItem);

  let prev: number | null;
  let next: number | null;

  if (currentIndex === 0) {
    prev = null;
    next = currentIndex + 1;
  } else if (currentIndex === allLinks.length - 1) {
    prev = currentIndex - 1;
    next = null;
  } else {
    prev = currentIndex - 1;
    next = currentIndex + 1;
  }

  return (
    <nav className="mt-8 mb-4 border-t border-gray-200 px-4 flex items-center justify-between sm:px-0">
      {prev !== null && allLinks[prev] && (
        <div className="w-0 flex-1 flex">
          <VersionedLink href={allLinks[prev].path}>
            <a className="-mt-px border-t-2 border-transparent pt-4 pr-1 inline-flex items-center text-sm leading-5 font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300 focus:outline-none focus:text-gray-700 focus:border-gray-400 transition ease-in-out duration-150">
              <svg
                className="mr-3 h-5 w-5 text-gray-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M7.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l2.293 2.293a1 1 0 010 1.414z"
                  clipRule="evenodd"
                />
              </svg>
              {allLinks[prev].name}
            </a>
          </VersionedLink>
        </div>
      )}

      {next !== null && allLinks[next] && (
        <div className="w-0 flex-1 flex justify-end">
          <VersionedLink href={allLinks[next].path}>
            <a className="-mt-px border-t-2 border-transparent pt-4 pl-1 inline-flex items-center text-sm leading-5 font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300 focus:outline-none focus:text-gray-700 focus:border-gray-400 transition ease-in-out duration-150">
              {allLinks[next].name}
              <svg
                className="ml-3 h-5 w-5 text-gray-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </a>
          </VersionedLink>
        </div>
      )}
    </nav>
  );
};
