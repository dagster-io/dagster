// import Link from "next/link";
import { useRouter } from 'next/router';
import data from 'data/searchindex.json';

import { contents as CONTENTS } from './contents.json';
import subTree from './subTree';

const API_DOCS_PAGES = [];

const docnames = data.docnames;
for (const i in docnames) {
  const doc = docnames[i];
  const title = data.titles[i];
  if (doc.includes('sections')) {
    API_DOCS_PAGES.push({
      name: title,
      path: doc.replace('sections/api/apidocs/', '/'),
    });
  }
}

export type TreeElement = {
  name: string;
  path: string;
  isAbsolutePath?: boolean;
};

const SUBTREE = subTree(API_DOCS_PAGES as TreeElement[]);

const MainItem: React.FunctionComponent<{
  name: string;
  path: string;
}> = ({ name, path }) => {
  const router = useRouter();
  const selected = router.pathname.includes(path);

  if (selected) {
    return (
      <a
        href="#"
        className="group flex items-center px-3 py-2 text-sm leading-5 font-medium text-gray-900 rounded-md bg-gray-100 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:bg-gray-200 transition ease-in-out duration-150"
      >
        <svg
          className="flex-shrink-0 -ml-1 mr-3 h-6 w-6 text-gray-500 group-hover:text-gray-500 group-focus:text-gray-600 transition ease-in-out duration-150"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M3 12l9-9 9 9M5 10v10a1 1 0 001 1h3a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1h3a1 1 0 001-1V10M9 21h6"
          />
        </svg>
        <span className="truncate">{name}</span>
      </a>
    );
  } else {
    return (
      <a
        href={path}
        className="mt-1 group flex items-center px-3 py-2 text-sm leading-5 font-medium text-gray-600 rounded-md hover:text-gray-900 hover:bg-gray-50 focus:outline-none focus:bg-gray-100 transition ease-in-out duration-150"
      >
        <svg
          className="flex-shrink-0 -ml-1 mr-3 h-6 w-6 text-gray-400 group-hover:text-gray-500 group-focus:text-gray-500 transition ease-in-out duration-150"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
          />
        </svg>
        <span className="truncate">{name}</span>
      </a>
    );
  }
};

const Sidebar = () => {
  const router = useRouter();
  const selectedSection = CONTENTS.find((i) =>
    router.pathname.includes(i.path),
  );

  return (
    <nav className="overflow-scroll left-bar">
      <div>
        <MainItem name={'Install'} path="/docs/install" />
        <MainItem name={'Tutorial'} path="/docs/tutorial" />
        <MainItem name={'Learn'} path="/docs/learn" />
        <MainItem name={'API Docs'} path="/docs/apidocs" />
        <MainItem name={'Deploying'} path="/docs/deploying" />
        <MainItem name={'Community'} path="/docs/community" />
      </div>
      <div className="mt-8">
        <h3 className="px-3 text-xs leading-4 font-semibold text-gray-500 uppercase tracking-wider">
          {selectedSection?.name}
        </h3>
        <div className="mt-1">
          {selectedSection?.name &&
            SUBTREE[selectedSection.name] &&
            SUBTREE[selectedSection.name].map((i: any) => {
              let subsectionPath = '';
              let subSelected = false;

              if (i.isAbsolutePath === true) {
                subsectionPath = i.path;
              } else {
                subsectionPath = selectedSection.path + i.path;
                if (router.pathname.includes(subsectionPath)) {
                  subSelected = true;
                }
                // Handle dynamic docs
                if (
                  router.query.page instanceof Array &&
                  '/' + router.query.page.join('/') === i.path
                ) {
                  subSelected = true;
                }
              }

              return (
                <a
                  href={subsectionPath}
                  className={`group flex items-center px-3 py-2 text-sm leading-5 font-medium text-gray-600 ${
                    subSelected && 'bg-blue-100'
                  } rounded-md hover:text-gray-900 hover:bg-gray-50 focus:outline-none focus:bg-gray-100 transition ease-in-out duration-150`}
                >
                  <span className="truncate">{i.name}</span>
                </a>
              );
            })}
        </div>
      </div>
    </nav>
  );
};

export default Sidebar;
