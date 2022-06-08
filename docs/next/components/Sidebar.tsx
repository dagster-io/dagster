import React from "react";

import { Transition } from "@headlessui/react";

import { Search } from "components/Search";
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
interface FancyButtonProps {
  item: any;
  match: boolean;
  lvl: number;
  href?: string;
}

const MenuItem = React.forwardRef<
  HTMLAnchorElement,
  React.PropsWithChildren<FancyButtonProps>
>(({ item, match, lvl, href }, ref) => {
  const rightIcon = item.isExternalLink
    ? Icons["ExternalLink"]
    : item.children && (match ? Icons["ChevronDown"] : Icons["ChevronRight"]);

  return (
    <a
      className={cx(
        "transition group flex justify-between items-center font-medium rounded-md text-gray-800 dark:text-gray-200",
        {
          "hover:bg-lavender hover:bg-opacity-50 text-blurple": match,
          "hover:text-gray-900 hover:bg-lavender hover:bg-opacity-50": !match,
          "px-2": lvl === 0,
          "pl-3 pr-2": lvl <= 1,
          "py-2": lvl <= 2,
        }
      )}
      href={href}
      ref={ref}
      target={item.isExternalLink ? "_blank" : "_self"}
      rel="noopener noreferrer"
    >
      <div className="flex justify-start">
        {item.icon && (
          <svg
            className={cx("mr-3 h-6 w-6 text-gray-400 transition", {
              "text-blurple": match,
              "group-hover:text-gray-600": !match,
            })}
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            {Icons[item.icon]}
          </svg>
        )}
        <span>{item.title}</span>
      </div>

      {rightIcon && (
        <svg
          className={cx("mr-2 h-4 w-4 text-gray-400 transition flex-shrink-0", {
            "text-blurple": match,
            "group-hover:text-gray-600": !match,
          })}
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          {rightIcon}
        </svg>
      )}
    </a>
  );
});

const TopLevelNavigation = () => {
  const navigation = useNavigation();
  const currentSection = getCurrentSection(navigation);

  return (
    <div className="space-y-1">
      {navigation.map((item) => {
        const match = item == currentSection;

        return (
          <div key={item.path}>
            {item.isExternalLink || item.isUnversioned ? (
              <MenuItem href={item.path} item={item} match={match} lvl={0} />
            ) : (
              <Link href={item.path} passHref>
                <MenuItem item={item} match={match} lvl={0} />
              </Link>
            )}
            {match && (
              <div className="mt-2">
                <div
                  className="ml-1"
                  role="group"
                  aria-labelledby="second-level-nav"
                >
                  <div className="border-l ml-5">
                    <SecondaryNavigation />
                  </div>
                </div>
              </div>
            )}
          </div>
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
      {currentSection.children.map((sectionOrItem) => {
        const match =
          sectionOrItem.path === asPathWithoutAnchor ||
          (sectionOrItem.children &&
            sectionOrItem.children.find(
              (item) => item.path === asPathWithoutAnchor
            ));

        const itemWithPath = sectionOrItem.path
          ? sectionOrItem
          : sectionOrItem.children[0];

        return (
          <div key={itemWithPath.path}>
            {itemWithPath.isExternalLink || itemWithPath.isUnversioned ? (
              <MenuItem
                href={itemWithPath.path}
                item={sectionOrItem}
                match={match}
                lvl={1}
              />
            ) : (
              <Link href={itemWithPath.path} passHref>
                <MenuItem item={sectionOrItem} match={match} lvl={1} />
              </Link>
            )}
            {match && sectionOrItem.children && (
              <div className="border-l ml-5 mt-2">
                <div
                  className="mt-1 ml-1 space-y-1"
                  role="group"
                  aria-labelledby="third-level-nav"
                >
                  {sectionOrItem.children.map((section) => {
                    return (
                      <ThirdLevelNavigation
                        key={section.title}
                        section={section}
                      />
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </>
  );
};

const ThirdLevelNavigation = ({ section }) => {
  const { asPathWithoutAnchor } = useVersion();

  return (
    <Link key={section.path} href={section.path}>
      <a
        className={cx(
          "group flex items-center px-3 py-1 text-sm text-gray-700 rounded-md",
          {
            "hover:bg-lavender hover:bg-opacity-50 text-blurple":
              section.path === asPathWithoutAnchor,
            "hover:text-gray-900 hover:bg-lavender hover:bg-opacity-50":
              section.path !== asPathWithoutAnchor,
          }
        )}
      >
        <span>{section.title}</span>
      </a>
    </Link>
  );
};

const SidebarContents = () => {
  return (
    <>
      {/* Sidebar component, swap this element with another sidebar if you like */}
      {/* Search Bar*/}
      <div className="h-0 flex-1 flex flex-col overflow-y-auto ">
        <div className="px-3 mt-5">
          <div className="block w-full pl-4 border-gray-300 rounded-full border bg-white">
            <Search />
          </div>
        </div>
        {/* End Search Bar */}

        {/* Navigation */}
        <nav className="px-3 mt-6">
          <TopLevelNavigation />
        </nav>
      </div>
    </>
  );
};

const Sidebar = ({ isMobileDocsMenuOpen, closeMobileDocsMenu }) => {
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
      <div className="hidden lg:block lg:flex-shrink-0">
        <div className="h-full flex flex-col w-80">
          <SidebarContents />
        </div>
      </div>
    </>
  );
};

export default Sidebar;
