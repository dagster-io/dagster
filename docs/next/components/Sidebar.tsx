import {Transition} from '@headlessui/react';
import cx from 'classnames';
import {Search} from 'components/Search';
import NextLink from 'next/link';
import React, {useState} from 'react';

import Icons from '../components/Icons';
import navigation, {flatten, getNavKey, getNavLvl} from '../util/navigation';
import {usePath} from '../util/usePath';

const useCurrentSection = (navigation) => {
  const {asPath} = usePath();
  const match = navigation.find((item) => item.path !== '/' && asPath.startsWith(item.path));
  return match || navigation.find((item) => item.path === '/');
};

interface MenuItemProps {
  item: any;
  match: boolean;
  lvl: number;
  onClick: () => void;
  expanded: boolean;
}

const MenuItem = React.forwardRef<HTMLAnchorElement, React.PropsWithChildren<MenuItemProps>>(
  ({item, match, lvl, onClick, expanded}, ref) => {
    const rightIcon = () => {
      if (item.isExternalLink) {
        return <ExternalLinkIcon match={match} />;
      }
      if (item.children) {
        return <ChevronButton expanded={expanded} match={match} onClick={() => onClick()} />;
      }
      return null;
    };

    const itemClassName = cx('relative transition rounded-md select-none', {
      'hover:bg-lavender hover:bg-opacity-50': match,
      'hover:text-gray-900 hover:bg-lavender hover:bg-opacity-50': !match,
    });

    const innerClassName = cx(
      'w-full relative transition group flex justify-between items-center text-gray-800 text-left select-none',
      {
        'text-blurple': match,
        'px-2 py-2 pl-3 pr-2 font-medium': lvl === 0,
        'py-2 ml-0 pl-2 pr-2 font-normal text-gray-500': lvl >= 1,
        'text-sm content-box w-full ': lvl >= 2,
      },
    );

    const itemContents = (
      <>
        <div className="flex justify-start content-box w-full">
          {item.icon && (
            <div
              className={cx('mr-2 h-6 w-6 text-gray-500 transition align-items-center', {
                'text-blurple': match,
                'group-hover:text-gray-700': !match,
              })}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="currentColor"
                viewBox="0 0 24 24"
                stroke="none"
                aria-hidden="true"
              >
                {Icons[item.icon]}
              </svg>
            </div>
          )}
          <span className="font-normal">{item.title}</span>
        </div>
      </>
    );

    if (item.path === undefined) {
      return (
        <div className={itemClassName}>
          <button className={innerClassName} onClick={onClick}>
            {itemContents}
          </button>
          {rightIcon()}
        </div>
      );
    }

    const linkElement = (
      <div className={itemClassName}>
        <a
          className={innerClassName}
          href={item.path}
          ref={ref}
          target={item.isExternalLink ? '_blank' : '_self'}
          rel="noopener noreferrer"
          onClick={onClick}
        >
          {itemContents}
        </a>
        {rightIcon()}
      </div>
    );

    if (item.isExternalLink) {
      return linkElement;
    }

    return (
      <NextLink href={item.path} passHref legacyBehavior>
        {linkElement}
      </NextLink>
    );
  },
);

const ExternalLinkIcon = ({match}: {match: boolean}) => {
  return (
    <div className="absolute right-0 top-1">
      <svg
        className={cx('mr-2 h-6 w-6 p-1 rounded-full text-gray-400 transition flex-shrink-0', {
          'text-blurple': match,
          'group-hover:text-gray-600': !match,
        })}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        {Icons.ExternalLink}
      </svg>
    </div>
  );
};

const ChevronButton = ({
  expanded,
  match,
  onClick,
}: {
  expanded: boolean;
  match: boolean;
  onClick: () => void;
}) => {
  // Disallow any NextLink wrapper from handling the click as it bubbles.
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    onClick();
  };

  return (
    <button onClick={handleClick} className="absolute right-2 top-2 p-2 -m-2">
      <svg
        className={cx('h-6 w-6 p-1 rounded-full text-gray-400 transition flex-shrink-0', {
          'text-blurple': match,
          'group-hover:text-gray-600': !match,
          'rotate-90': expanded,
        })}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        {expanded || match ? Icons.ChevronDown : Icons.ChevronRight}
      </svg>
    </button>
  );
};

const RecursiveNavigation = ({
  itemOrSection,
  parentKey,
  idx,
  navKeysToExpanded,
  setNavKeysToExpanded,
}) => {
  const {asPathWithoutAnchor} = usePath();
  const currentSection = useCurrentSection(navigation);
  const navKey = getNavKey(parentKey, idx);
  const lvl = getNavLvl(navKey);

  const onClick = (key) => {
    setNavKeysToExpanded((prevState) => {
      const updatedValues = {[key]: !prevState[key]};
      return {...prevState, ...updatedValues};
    });
  };

  // Note: this logic is based on path which could be improved by having parent info in itemOrSection
  const match =
    itemOrSection === currentSection ||
    itemOrSection.path === asPathWithoutAnchor ||
    (itemOrSection.children &&
      itemOrSection.children.find((item) => asPathWithoutAnchor.startsWith(item.path)));

  const expanded = Boolean(navKeysToExpanded[navKey]);

  // Display item
  if (!itemOrSection?.children) {
    return (
      <MenuItem
        item={itemOrSection}
        match={match}
        lvl={lvl}
        onClick={() => onClick(navKey)}
        expanded={expanded}
      />
    );
  }

  // Display section
  return (
    <div
      className={cx({
        'mt-0 ml-1 space-y-0': lvl >= 2,
      })}
      role="group"
      aria-labelledby={`${lvl + 1}-level-nav`}
    >
      <MenuItem
        item={itemOrSection}
        match={match}
        lvl={lvl}
        onClick={() => onClick(navKey)}
        expanded={expanded}
      />
      {(expanded || match) &&
        itemOrSection.children.map((item, idx) => {
          return (
            <div className="border-l ml-6" key={idx}>
              <RecursiveNavigation
                key={idx}
                itemOrSection={item}
                parentKey={navKey}
                idx={idx}
                navKeysToExpanded={navKeysToExpanded}
                setNavKeysToExpanded={setNavKeysToExpanded}
              />
            </div>
          );
        })}
    </div>
  );
};

const TopLevelNavigation = () => {
  const map = {};
  const [navKeysToExpanded, setNavKeysToExpanded] = useState<{
    [key: string]: boolean;
  }>(
    flatten(navigation).reduce((map, obj) => {
      map[obj.key] = obj.isDefaultOpen;
      return map;
    }, map),
  );

  return (
    <div className="space-y-1">
      {navigation.map((itemOrSection, idx) => {
        return (
          <RecursiveNavigation
            key={idx}
            itemOrSection={itemOrSection}
            parentKey=""
            idx={idx}
            navKeysToExpanded={navKeysToExpanded}
            setNavKeysToExpanded={setNavKeysToExpanded}
          />
        );
      })}
    </div>
  );
};

const SidebarContents = () => {
  return (
    <>
      {/* Sidebar component, swap this element with another sidebar if you like */}
      {/* Search Bar*/}
      <div className="flex-1 flex flex-col">
        <div className="px-3 mt-5">
          <div className="block w-full pl-4 border-gray-200 rounded-full border bg-white">
            <Search />
          </div>
        </div>
        {/* End Search Bar */}

        {/* Navigation */}
        <nav className="px-3 mt-6 overflow-y-scroll max-h-screen pb-64">
          <TopLevelNavigation />
        </nav>
      </div>
    </>
  );
};

const Sidebar = ({isMobileDocsMenuOpen, closeMobileDocsMenu}) => {
  return (
    <>
      {/* Off-canvas menu for mobile, show/hide based on off-canvas menu state. */}
      <Transition show={isMobileDocsMenuOpen}>
        <div className="lg:hidden">
          <div className="fixed inset-0 flex z-50">
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
                      onClick={closeMobileDocsMenu}
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
      <div className="hidden lg:block fixed left-8 z-40 lg:flex-shrink-0">
        <div className="h-full flex flex-col w-80">
          <SidebarContents />
        </div>
      </div>
    </>
  );
};

export default Sidebar;
