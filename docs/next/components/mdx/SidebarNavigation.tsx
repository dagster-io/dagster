import { useEffect, useState } from "react";

import cx from "classnames";

// By parsing the AST, we generate a sidebar navigation tree like this:
//
// {"items": [{
//   "url": "#something-if",
//   "title": "Something if",
//   "items": [
//     {
//       "url": "#something-else",
//       "title": "Something else"
//     },
//     {
//       "url": "#something-elsefi",
//       "title": "Something elsefi"
//     }
//   ]},
//   {
//     "url": "#something-iffi",
//     "title": "Something iffi"
//   }]}

// Given the tree, get all the IDS
const getIds = (items) => {
  return items.reduce((acc, item) => {
    if (item.url) {
      // url has a # as first character, remove it to get the raw CSS-id
      acc.push(item.url.slice(1));
    }
    if (item.items) {
      acc.push(...getIds(item.items));
    }
    return acc;
  }, []);
};

// Calculate the ID currently on the page to highlight it
const useActiveId = (itemIds) => {
  const [activeId, setActiveId] = useState(`test`);
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        });
      },
      { rootMargin: `0% 0% -95% 0%` }
    );
    itemIds.forEach((id) => {
      if (document.getElementById(id)) {
        observer.observe(document.getElementById(id));
      }
    });
    return () => {
      itemIds.forEach((id) => {
        if (document.getElementById(id)) {
          observer.unobserve(document.getElementById(id));
        }
      });
    };
  }, [itemIds]);
  return activeId;
};

const MARGINS = ["ml-0", "ml-4", "ml-8", "ml-12"];

const renderItems = (items, activeId, depth) => {
  return (
    <ol>
      {items.map((item) => {
        return (
          <li key={item.url} className={cx(MARGINS[depth], "mt-3 list-inside")}>
            <a
              href={item.url}
              className={cx("font-semibold text-sm", {
                "text-gray-800 dark:text-gray-100 underline bg-blue-50 dark:bg-blue-900":
                  activeId === item.url.slice(1),
                "text-gray-500 dark:text-gray-300":
                  activeId !== item.url.slice(1),
              })}
            >
              {item.title}
            </a>
            {item.items && renderItems(item.items, activeId, depth + 1)}
          </li>
        );
      })}
    </ol>
  );
};

const SidebarNavigation = ({ items }) => {
  if (!items) {
    return null;
  }
  const idList = getIds(items);
  const activeId = useActiveId(idList);
  return renderItems(items, activeId, 0);
};

export default SidebarNavigation;
