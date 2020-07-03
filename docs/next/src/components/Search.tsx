// import Link from "next/link";
import {
  InstantSearch,
  connectSearchBox,
  connectHits,
} from 'react-instantsearch-dom';
import useClickAway from 'react-use/lib/useClickAway';
import { useState, useRef, Dispatch, SetStateAction } from 'react';
import algoliasearch from 'algoliasearch/lite';
import { SearchBoxProvided } from 'react-instantsearch-core';
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
        href={'/_apidocs/' + hit.path}
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

type SearchBoxFocusProp = {
  onFocusChange: (focus: boolean) => void;
};

type SearchBoxProps = SearchBoxProvided & SearchBoxFocusProp;

const SearchBox: React.FC<SearchBoxProps> = ({
  currentRefinement,
  refine,
  onFocusChange,
}) => {
  const handleInputFocus = () => {
    onFocusChange(true);
  };
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
          onFocus={handleInputFocus}
          value={currentRefinement}
          onChange={(event) => refine(event.currentTarget.value)}
        />
      </div>
    </div>
  );
};

const CustomSearchBox = connectSearchBox<SearchBoxProps>(
  ({ currentRefinement, refine, isSearchStalled, onFocusChange }) => (
    <SearchBox
      onFocusChange={onFocusChange}
      isSearchStalled={isSearchStalled}
      currentRefinement={currentRefinement}
      refine={refine}
    />
  ),
);

const Search = () => {
  const [focus, setFocus] = useState(false);

  const ref = useRef(null);
  useClickAway(ref, () => {
    setFocus(false);
  });

  const CustomHits = connectHits(Hits);

  return (
    <InstantSearch
      indexName="docs"
      searchClient={searchClient}
      createURL={(searchState) => console.log(searchState.query)}
    >
      <div
        ref={ref}
        className="relative flex-1 flex items-center justify-center px-2 lg:ml-6 lg:justify-end"
      >
        <CustomSearchBox onFocusChange={(focusValue) => setFocus(focusValue)} />
        &nbsp;
        {focus && (
          <div className="top-14 fixed right-0 max-w-full md:absolute md:w-2/3 z-10">
            <CustomHits />
          </div>
        )}
      </div>
    </InstantSearch>
  );
};

export default Search;
