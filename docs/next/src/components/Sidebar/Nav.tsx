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
  const treeOfContents = useTreeOfContents();
  const router = useRouter();
  const allLinks = flatten(Object.values(treeOfContents), true);
  const selectedSection = allLinks.find((l) => router.asPath.includes(l.path));
  const selectedSectionChildren = (treeOfContents as Record<string, any>)[
    selectedSection?.name || ''
  ]?.children;

  return (
    <nav className={className}>
      {isMobile && <CommunityLinks className="mb-5" />}
      <div className="border-b border-gray-200 pb-2">
        {Object.values(treeOfContents).map((element) => (
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
          <h3 className="px-3 text-xs leading-4 font-semibold text-gray-500 uppercase tracking-wider">
            {selectedSection.name}
          </h3>
          <div className="mt-1">
            {selectedSectionChildren.map((c: TreeLink) => {
              const subSelected =
                router.asPath.startsWith(c.path) &&
                router.asPath.length - c.path.length < 2;

              return (
                <VersionedLink key={`${c.path}-${c.name}`} href={c.path}>
                  <a
                    className={cx(
                      `group flex justify-between items-center px-3 py-2 text-sm leading-5 font-medium text-gray-600 rounded-md focus:outline-none transition ease-in-out duration-150`,
                      {
                        'font-semibold text-blue-700 bg-blue-100': subSelected,
                        'hover:font-semibold': !subSelected,
                      },
                    )}
                  >
                    <div className="truncatej">{c.name}</div>
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
                  </a>
                </VersionedLink>
              );
            })}
          </div>
        </div>
      ) : null}
    </nav>
  );
};

export default Nav;
