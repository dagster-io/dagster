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

const MenuItem = ({ item, match, lvl, href = null }) => {
  const rightIcon = item.isExternalLink
    ? Icons["ExternalLink"]
    : item.children && (match ? Icons["ChevronDown"] : Icons["ChevronRight"]);

  return (
    <a
      className={cx(
        "transition group flex justify-between items-center text-md font-medium rounded-md text-gray-800 dark:text-gray-200",
        {
          "hover:bg-lavender hover:bg-opacity-50 text-blurple": match,
          "hover:text-gray-900 hover:bg-lavender hover:bg-opacity-50": !match,
          "py-2": lvl <= 2,
          "px-2": lvl === 0,
          "pl-3 pr-2": lvl === 2,
        }
      )}
      href={href}
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
        <span
          className={cx({
            "DocSearch-lvl0": lvl === 0 && match,
            "DocSearch-lvl2": lvl === 2 && match,
          })}
        >
          {item.title}
        </span>
      </div>

      {rightIcon && (
        <svg
          className={cx("mr-2 h-4 w-4 text-gray-400 transition", {
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
};

const TopLevelNavigation = () => {
  const navigation = useNavigation();
  const currentSection = getCurrentSection(navigation);

  return (
    <div className="space-y-1">
      {navigation.map((item) => {
        const match = item == currentSection;

        return (
          <>
            {item.isExternalLink ? (
              <MenuItem
                key={item.path}
                href={item.path}
                item={item}
                match={match}
                lvl={0}
              />
            ) : (
              <Link key={item.path} href={item.path} passHref>
                <MenuItem item={item} match={match} lvl={0} />
              </Link>
            )}
            {/* <Link key={item.path} href={item.path}>
              <a
                className={cx(
                  "transition group flex justify-between items-center px-2 py-2 text-md font-medium rounded-md text-gray-800 dark:text-gray-200",
                  {
                    "hover:bg-lavender hover:bg-opacity-50 text-blurple": match,
                    "hover:text-gray-900 hover:bg-lavender hover:bg-opacity-50":
                      !match,
                  }
                )}
              >
                <div className="flex justify-start">
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
                  <span className={cx({ "DocSearch-lvl0": match })}>
                    {item.title}
                  </span>
                </div>

                {rightIcon && (
                  <svg
                    className={cx("mr-2 h-4 w-4 text-gray-400 transition", {
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
            </Link> */}
            {match && (
              <div key={item.title} className="mt-8">
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
          </>
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
          sectionOrItem.children &&
          sectionOrItem.children.find(
            (sectionOrItem) => sectionOrItem.path == asPathWithoutAnchor
          );

        const rightIcon = sectionOrItem.isExternalLink
          ? Icons["ExternalLink"]
          : sectionOrItem.children &&
            (match ? Icons["ChevronDown"] : Icons["ChevronRight"]);

        return (
          <>
            {sectionOrItem.isExternalLink ? (
              <MenuItem
                key={sectionOrItem.path || sectionOrItem.children[0].path}
                href={sectionOrItem.path || sectionOrItem.children[0].path}
                item={sectionOrItem}
                match={match}
                lvl={2}
              />
            ) : (
              <Link
                key={sectionOrItem.path || sectionOrItem.children[0].path}
                href={sectionOrItem.path || sectionOrItem.children[0].path}
                passHref
              >
                <MenuItem item={sectionOrItem} match={match} lvl={2} />
              </Link>
            )}
            {/* <Link
              key={sectionOrItem.path}
              href={sectionOrItem.path || sectionOrItem.children[0].path}
            >
              <a
                className={cx(
                  "group flex justify-between items-center px-3 py-2 text-md font-medium text-gray-700",
                  {
                    "hover:bg-lavender hover:bg-opacity-50 text-blurple":
                      sectionOrItem.path === asPathWithoutAnchor,
                    "hover:text-gray-900 hover:bg-lavender hover:bg-opacity-50":
                      sectionOrItem.path !== asPathWithoutAnchor,
                  }
                )}
              >
                <span
                  className={cx({
                    "DocSearch-lvl2":
                      sectionOrItem.path === asPathWithoutAnchor,
                  })}
                >
                  {sectionOrItem.title}
                </span>

                {rightIcon && (
                  <svg
                    className={cx("mr-1 h-4 w-4 text-gray-400 transition", {
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
            </Link> */}

            {match && (
              <div key={sectionOrItem.title} className="border-l ml-5 mt-2">
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
          </>
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
          "group flex items-center px-3 py-1 text-sm text-gray-700 rounded-md",
          {
            "hover:bg-lavender hover:bg-opacity-50 text-blurple":
              section.path === asPathWithoutAnchor,
            "hover:text-gray-900 hover:bg-lavender hover:bg-opacity-50":
              section.path !== asPathWithoutAnchor,
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

const Sidebar = ({ isMobileMenuOpen, closeMobileMenu }) => {
  return (
    <>
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
