// import Link from "next/link";
import algoliasearch from 'algoliasearch/lite';
import {
  InstantSearch,
  connectSearchBox,
  connectHits,
} from 'react-instantsearch-dom';
import useClickAway from 'react-use/lib/useClickAway';

import { useState, useRef } from 'react';
import CommunityLinks from './CommunityLinks';

const searchClient = algoliasearch(
  // TODO: Move to next environment variables: https://nextjs.org/docs/api-reference/next.config.js/environment-variables
  // It's okay that this is in source control for now, since these are
  // client facing variables.
  'CTO1CV9T4R',
  '991c27897aafec73e6eff85912eed810',
);

const Hit: React.FunctionComponent<{ hit: any }> = ({ hit }) => {
  const colors: {
    [key: string]: string;
  } = {
    attribute: 'yellow',
    class: 'blue',
    method: 'red',
    exception: 'red',
    function: 'green',
    module: 'purple',
    data: 'teal',
    cmdoptoin: 'pink',
  };

  return (
    <li className="border-b border-gray-100">
      <a
        href={'/docs/apidocs/' + hit.path}
        className="block hover:bg-gray-50 focus:outline-none focus:bg-gray-50 transition duration-150 ease-in-out"
      >
        <div className="px-4 py-4 sm:px-6">
          <div className="flex items-center justify-between">
            <code className="text-sm leading-5 font-medium text-indigo-600 font-semibold truncate">
              {hit.object}
            </code>
            <div className="ml-2 flex-shrink-0 flex">
              <code
                className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-${
                  colors[hit.type]
                }-100 text-${colors[hit.type]}-800`}
              >
                {hit.type}
              </code>
            </div>
          </div>
          <div className="mt-2 sm:flex sm:justify-between">
            <div className="sm:flex">
              <div className="mt-2 flex items-center text-sm leading-5 text-gray-500 sm:mt-0">
                {hit.type === 'cmdoption'
                  ? `cli: ${hit.module.split('-').join(' ')}`
                  : hit.module}
              </div>
            </div>
          </div>
        </div>
      </a>
    </li>
  );
};

const Hits: React.FunctionComponent<{ hits: any[] }> = ({ hits }) => {
  return (
    <div className="bg-white border shadow overflow-hidden sm:rounded-md">
      <ul>
        {hits.splice(0, 6).map((hit) => (
          <Hit hit={hit} />
        ))}
      </ul>
    </div>
  );
};

const Search = () => {
  const ref = useRef(null);

  const [focus, setFocus] = useState(false);
  useClickAway(ref, () => {
    setFocus(false);
  });

  const CustomSearchBox = connectSearchBox(
    // @ts-ignore
    ({ setFocus, currentRefinement, refine }) => (
      <SearchBox
        currentRefinement={currentRefinement}
        refine={refine}
        setFocus={setFocus}
      />
    ),
  );

  const CustomHits = connectHits(Hits);

  return (
    <InstantSearch
      indexName="docs"
      searchClient={searchClient}
      createURL={(searchState) => console.log(searchState.query)}
    >
      <div
        className="relative flex-1 flex items-center justify-center px-2 lg:ml-6 lg:justify-end"
        ref={ref}
      >
        <CustomSearchBox
          // @ts-ignore:
          setFocus={setFocus}
        />
        &nbsp;
        {focus && (
          <div className="top-14 fixed right-0 max-w-full md:right-auto md:absolute md:w-2/3 z-10">
            <CustomHits />
          </div>
        )}
      </div>
    </InstantSearch>
  );
};

const SearchBox: React.FC<{
  refine: (...args: any[]) => any;
  currentRefinement: string;
  setFocus: any;
}> = ({ currentRefinement, refine, setFocus }) => {
  return (
    <div className="max-w-lg w-full lg:max-w-xs">
      <label htmlFor="search" className="sr-only">
        Search
      </label>
      <div className="relative">
        <div className="hidden md:flex absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg
            className="h-5 w-5 text-gray-400"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <input
          id="search"
          className="block w-full pl-2 md:pl-10 pr-2 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:border-blue-300 focus:shadow-outline-blue sm:text-sm transition duration-150 ease-in-out"
          placeholder="Search"
          type="search"
          onFocus={() => setFocus(true)}
          value={currentRefinement}
          onChange={(event) => refine(event.currentTarget.value)}
        />
      </div>
    </div>
  );
};

type HeaderProps = {
  onMobileToggleNavigationClick: () => void;
};

const Header: React.FC<HeaderProps> = ({ onMobileToggleNavigationClick }) => {
  return (
    <nav className="bg-white border-b border-gray-200 shadow">
      <div className="mx-auto px-2 sm:px-4 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex px-2 lg:px-0">
            <div className="flex-shrink-0 flex items-center">
              <img
                className="block mt-2 lg:hidden h-8 w-auto"
                src="/assets/logos/small.png"
                alt="Logo"
              />
              <img
                className="hidden mt-2 lg:block h-8 w-auto"
                src="/assets/logos/large.png"
                alt="Logo"
              />
            </div>
            <div className="ml-6 flex">
              <a
                href="#"
                className="inline-flex items-center px-1 pt-1 border-b-2 border-indigo-500 text-sm font-medium leading-5 text-gray-900 focus:outline-none focus:border-indigo-700 transition duration-150 ease-in-out"
              >
                Docs
              </a>
              <a
                href="#"
                className="ml-2 lg:ml-8 inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium leading-5 text-gray-500 hover:text-gray-700 hover:border-gray-300 focus:outline-none focus:text-gray-700 focus:border-gray-300 transition duration-150 ease-in-out"
              >
                Blog
              </a>
              <a
                href="#"
                className="ml-2 lg:ml-8 inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium leading-5 text-gray-500 hover:text-gray-700 hover:border-gray-300 focus:outline-none focus:text-gray-700 focus:border-gray-300 transition duration-150 ease-in-out"
              >
                Community
              </a>
            </div>
          </div>
          <Search />
          <div className="flex items-center lg:hidden">
            <button
              onClick={() => onMobileToggleNavigationClick()}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:bg-gray-100 focus:text-gray-500 transition duration-150 ease-in-out"
            >
              {/* <!-- Icon when menu is closed. -->
          <!-- Menu open: "hidden", Menu closed: "block" --> */}
              <svg
                className="block h-6 w-6"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
              {/* <!-- Icon when menu is open. -->
          <!-- Menu open: "block", Menu closed: "hidden" --> */}
              <svg
                className="hidden h-6 w-6"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <div className="hidden lg:ml-4 lg:flex lg:items-center">
            <CommunityLinks className="w-40" />
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Header;
