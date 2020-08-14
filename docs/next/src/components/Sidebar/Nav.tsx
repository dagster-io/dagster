import cx from 'classnames';
import { useRouter } from 'next/router';
import CommunityLinks from 'components/CommunityLinks';
import { flatten, TreeLink } from 'utils/treeOfContents/flatten';
import { useTreeOfContents } from 'hooks/useTreeOfContents';
import { VersionedLink } from 'components/VersionedComponents';

export type TreeElement = {
  name: string;
  path: string;
  isAbsolutePath?: boolean;
};

type MainItemProps = {
  name: string;
  path: string;
  icon?: JSX.Element;
};

const MainItem: React.FC<MainItemProps> = ({ name, path }) => {
  const router = useRouter();
  const selected = router.pathname.includes(path);
  return (
    <VersionedLink href={path}>
      <a
        className={cx(
          'group flex justify-between items-center px-2 py-2 text-sm font-medium leading-5 text-gray-900 rounded-md',
          { 'font-bold underline': selected },
          { 'hover:font-bold': !selected },
          'transition ease-in-out duration-150',
        )}
      >
        {/* {icon} */}
        <span className="truncate">{name}</span>
        <div
          className={cx(
            'w-2 h-2 rounded-full transition ease-in-out duration-600',
            {
              'bg-blue-300': selected,
            },
          )}
        ></div>
      </a>
    </VersionedLink>
  );
};

type NavProps = {
  className: string;
  isMobile?: boolean;
};

const Nav: React.FC<NavProps> = ({ className, isMobile }) => {
  let treeOfContents = useTreeOfContents();
  const router = useRouter();

  const isApiDocs = router.pathname.startsWith('/_apidocs');

  if (isApiDocs) {
    treeOfContents = treeOfContents.filter((i) => i.name === 'API Docs');
  } else {
    treeOfContents = treeOfContents.filter((i) => i.name !== 'API Docs');
  }

  const allLinks = flatten(treeOfContents, true);
  const selectedSection = allLinks.find((l) => router.asPath.includes(l.path));
  const selectedSectionChildren = treeOfContents.find(
    (entry) => entry.name === selectedSection?.name,
  )?.children;

  return (
    <nav className={className}>
      {isMobile && <CommunityLinks className="mb-5" />}
      <div className="border-b border-gray-200 pb-2">
        {treeOfContents.map((element) => (
          <MainItem
            key={element.name}
            name={element.name}
            path={element.path}
          />
        ))}
      </div>
      {selectedSection &&
      selectedSectionChildren &&
      selectedSectionChildren.length > 0 ? (
        <div className="mt-8">
          {!isApiDocs && (
            <h3 className="px-3 text-xs leading-4 font-semibold text-gray-500 uppercase tracking-wider">
              {selectedSection.name}
            </h3>
          )}
          <div className="mt-1">
            {selectedSectionChildren.map((c: TreeLink) => {
              const subSelected =
                router.asPath.startsWith(c.path) &&
                router.asPath.length - c.path.length < 2;

              const subHighlighted = subSelected && !c.childPath;

              const subChildSelected =
                (c.children &&
                  c.children.reduce((accumulator, child) => {
                    return (
                      accumulator ||
                      (router.asPath.startsWith(child.path) &&
                        router.asPath.length - child.path.length < 2)
                    );
                  }, false)) ||
                false;

              return (
                <div key={`${c.path}-${c.name}`}>
                  <VersionedLink href={c.path}>
                    <a
                      className={cx(
                        `group flex justify-between items-center px-3 py-2 text-sm leading-5 font-medium text-gray-600 rounded-md focus:outline-none transition ease-in-out duration-150`,
                        {
                          'font-semibold': subSelected,
                          'text-blue-700 bg-blue-100': subHighlighted,
                          'hover:font-semibold': !subSelected,
                        },
                      )}
                    >
                      <div className="truncate">{c.name}</div>
                      <div>
                        {c.isExternal && (
                          <svg
                            className="w-4 h-4 bg-gray-50"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"></path>
                            <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"></path>
                          </svg>
                        )}
                      </div>
                      {c.children && (
                        <div>
                          {subSelected || subChildSelected ? (
                            <svg
                              className="w-4 h-4 bg-gray-50"
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path
                                fillRule="evenodd"
                                d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                                clipRule="evenodd"
                              ></path>
                            </svg>
                          ) : (
                            <svg
                              className="w-4 h-4 bg-gray-50"
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path
                                fillRule="evenodd"
                                d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                                clipRule="evenodd"
                              ></path>
                            </svg>
                          )}
                        </div>
                      )}
                    </a>
                  </VersionedLink>
                  {(subSelected ||
                    subChildSelected ||
                    // always expand selections in 'API Docs'
                    selectedSection.name === 'API Docs') &&
                    c.children &&
                    c.children.map((child) => {
                      const childSelected =
                        router.asPath.startsWith(child.path) &&
                        router.asPath.length - child.path.length < 2;

                      return (
                        <div
                          className="ml-4 border-l"
                          key={`${child.path}-${child.name}`}
                        >
                          <VersionedLink href={child.path}>
                            <a
                              className={cx(
                                `group flex justify-between items-center px-3 py-2 text-sm leading-5 ml-1 font-medium text-gray-600 rounded-md focus:outline-none transition ease-in-out duration-150`,
                                {
                                  'font-semibold text-blue-700 bg-blue-100': childSelected,
                                  'hover:font-semibold': !childSelected,
                                },
                              )}
                            >
                              <div className="truncate">{child.name}</div>
                              <div>
                                {child.isExternal && (
                                  <svg
                                    className="w-4 h-4 bg-gray-50"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                  >
                                    <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"></path>
                                    <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"></path>
                                  </svg>
                                )}
                              </div>
                            </a>
                          </VersionedLink>
                        </div>
                      );
                    })}
                </div>
              );
            })}
          </div>
        </div>
      ) : null}
    </nav>
  );
};

export default Nav;
