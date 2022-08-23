import cx from 'classnames';
import {useEffect, useState} from 'react';
import visit from 'unist-util-visit';

// Travel the tree to get the headings
export function getItems(node, current) {
  if (!node) {
    return {};
  } else if (node.type === `paragraph`) {
    visit(node, (item) => {
      if (item.type === `link`) {
        const url: string = item['url'];
        // workaround for https://github.com/syntax-tree/mdast-util-toc/issues/70
        // remove ids of HTML elements from the headings, i.e. "experimental", "cross", "check"
        current.url = url
          .replace(/^#cross-/, '#')
          .replace(/^#check-/, '#')
          .replace(/-experimental-?$/, '');
      }
      if (item.type === `text`) {
        current.title = item['value'];
      }
    });
    return current;
  } else {
    if (node.type === `list`) {
      current.items = node.children.map((i) => getItems(i, {}));
      return current;
    } else if (node.type === `listItem`) {
      const heading = getItems(node.children[0], {});
      if (node.children.length > 1) {
        getItems(node.children[1], heading);
      }
      return heading;
    }
  }
  return {};
}

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
export const getIds = (items) => {
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
      {rootMargin: `0% 0% -50% 0%`},
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

const MARGINS = ['ml-0', 'ml-2', 'ml-4', 'ml-8'];

const renderItems = (items, activeId, depth, key) => {
  return (
    <ol key={key}>
      {items.map((item, idx) => {
        return item.url ? (
          <li key={`${key}-${idx}`} className={cx(MARGINS[depth], 'mt-3 list-inside')}>
            <a
              href={item.url}
              className={cx('font-semibold text-sm text-gray-500 hover:text-gray-800 transition', {
                'text-gray-800': activeId === item.url.slice(1),
                'text-gray-500 hover:text-gray-800 transition': activeId !== item.url.slice(1),
              })}
            >
              {item.title}
            </a>
            {item.items && renderItems(item.items, activeId, depth + 1, `${key}-${idx}`)}
          </li>
        ) : (
          renderItems(item.items, activeId, depth, `${key}-${idx}`)
        );
      })}
    </ol>
  );
};

const SidebarNavigation = ({items}) => {
  const idList = getIds(items);
  const activeId = useActiveId(idList);
  if (!items) {
    return null;
  }
  return renderItems(items, activeId, 0, 0);
};

export default SidebarNavigation;
