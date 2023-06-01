import cx from 'classnames';
import {useEffect, useState} from 'react';
import GitHubButton from 'react-github-btn';
import visit from 'unist-util-visit';

// ==============================
// handling Markdoc-style Markdown
// ==============================

export function collectHeadings(node, headings = []) {
  if (node) {
    if (node.name === 'Heading') {
      const title = node.children[0];

      if (typeof title === 'string') {
        headings.push({
          ...node.attributes,
          title,
        });
      }
    }

    if (node.children) {
      for (const child of node.children) {
        collectHeadings(child, headings);
      }
    }
  }
  return headings;
}

// ==============================
// handling MDX (will be deprecated)
// ==============================

// Travel the tree to get the headings
export function getMDXItems(node, current) {
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
      current.items = node.children.map((i) => getMDXItems(i, {}));
      return current;
    } else if (node.type === `listItem`) {
      const heading = getMDXItems(node.children[0], {});
      if (node.children.length > 1) {
        getMDXItems(node.children[1], heading);
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

const MARGINS = ['ml-0', 'ml-2', 'ml-4', 'ml-6'];

const renderItems = (items, activeId) => {
  return (
    <ol>
      {items.map((item, idx) => (
        <li key={`${idx}`} className={cx(MARGINS[item.level - 1], 'mt-2 list-inside ')}>
          <a
            href={item.url}
            className={cx(
              'font-normal text-sm text-gray-500 hover:text-gray-800 transition leading-2',
              {
                'text-blurple': activeId === item.id,
                'text-gray-500 hover:text-gray-800 transition': activeId !== item.id,
              },
            )}
          >
            {item.title}
          </a>
        </li>
      ))}
    </ol>
  );
};

export const SidebarNavigation = ({headings}) => {
  // handle Markdoc content
  const idList = headings.map((heading) => heading.id);
  const activeId = useActiveId(idList);

  if (!headings) {
    return null;
  }

  return renderItems(headings, activeId);
};

export const RightSidebar = ({
  editMode,
  headings = null,
  navigationItemsForMDX = null,
  githubLink,
  toggleFeedback,
}) => {
  return (
    !editMode && (
      <aside className="hidden relative xl:block flex-none w-80 shrink-0 border-l border-gray-200">
        {/* Start secondary column (hidden on smaller screens) */}
        <div className="flex flex-col justify-between top-24 px-2 sticky">
          <div
            className="mb-8 px-4 pb-10 relative overflow-y-scroll border-b border-gray-200"
            style={{maxHeight: 'calc(100vh - 300px)'}}
          >
            <div className="font-medium text-gable-green">On This Page</div>
            <div className="mt-4">
              {navigationItemsForMDX && <SidebarNavigationForMDX items={navigationItemsForMDX} />}
              {headings && <SidebarNavigation headings={headings} />}
            </div>
          </div>
          <div className="py-2 px-4 flex items-center group">
            <svg
              className="h-4 w-4 text-gray-500 dark:text-gray-300 group-hover:text-gray-800 dark:group-hover:text-gray-100 transition transform group-hover:scale-105 group-hover:rotate-6"
              role="img"
              viewBox="0 0 24 24"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
            </svg>
            <a
              className="text-sm ml-2 text-gray-500 dark:text-gray-300 group-hover:text-gray-800 dark:group-hover:text-gray-100"
              href={githubLink}
            >
              Edit Page on GitHub
            </a>
          </div>
          <div className="py-2 px-4 flex items-center group">
            <svg
              className="h-4 w-4 text-gray-500 dark:text-gray-300 group-hover:text-gray-800 dark:group-hover:text-gray-100 transition transform group-hover:scale-105 group-hover:rotate-6"
              role="img"
              viewBox="0 0 24 24"
              stroke="currentColor"
              fill="none"
              strokeWidth="2"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
              />
            </svg>
            <button
              className="text-sm ml-2 text-gray-500 dark:text-gray-300 group-hover:text-gray-800 dark:group-hover:text-gray-100"
              onClick={toggleFeedback}
            >
              Share Feedback
            </button>
          </div>
          <div className="py-2 px-4 flex items-center group">
            <GitHubButton
              href={process.env.NEXT_PUBLIC_DAGSTER_REPO_URL}
              data-icon="octicon-star"
              data-show-count="true"
              aria-label="Star dagster-io/dagster on GitHub"
            >
              Star
            </GitHubButton>
          </div>
        </div>
        {/* End secondary column */}
      </aside>
    )
  );
};

// ==============================
// handling MDX (will be deprecated)
// ==============================
const MDX_ITEM_MARGINS = ['ml-0', 'ml-1', 'ml-2', 'ml-3'];

const renderMDXItems = (items, activeId, depth, key) => {
  return (
    <ol key={key}>
      {items.map((item, idx) => {
        return item.url ? (
          <li key={`${key}-${idx}`} className={cx(MDX_ITEM_MARGINS[depth], 'mt-2 list-inside ')}>
            <a
              href={item.url}
              className={cx(
                'font-normal text-sm text-gray-500 hover:text-gray-800 transition leading-2',
                {
                  'text-blurple': activeId === item.url.slice(1),
                  'text-gray-500 hover:text-gray-800 transition': activeId !== item.url.slice(1),
                },
              )}
            >
              {item.title}
            </a>
            {item.items && renderMDXItems(item.items, activeId, depth + 1, `${key}-${idx}`)}
          </li>
        ) : (
          renderMDXItems(item.items, activeId, depth, `${key}-${idx}`)
        );
      })}
    </ol>
  );
};

export const SidebarNavigationForMDX = ({items}) => {
  // handle legacy MDX content

  const idList = getIds(items);
  const activeId = useActiveId(idList);

  if (!items) {
    return null;
  }
  return renderMDXItems(items, activeId, 0, 0);
};
