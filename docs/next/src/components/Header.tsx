// import Link from "next/link";
import algoliasearch from 'algoliasearch/lite';
import {
  InstantSearch,
  connectSearchBox,
  connectHits,
} from 'react-instantsearch-dom';
import useClickAway from 'react-use/lib/useClickAway';

import { useState, useRef } from 'react';

const searchClient = algoliasearch(
  // TODO: Move to next environment variables: https://nextjs.org/docs/api-reference/next.config.js/environment-variables
  // It's okay that this is in source control for now, since these are
  // client facing variables.
  'CTO1CV9T4R',
  '991c27897aafec73e6eff85912eed810',
);

// const linkStyle = {
//   marginRight: 15
// };

const SearchBox: React.FunctionComponent<{
  refine: (...args: any[]) => any;
  currentRefinement: string;
  setFocus: any;
}> = ({ currentRefinement, refine, setFocus }) => {
  return (
    <input
      onFocus={() => setFocus(true)}
      className="w-full bg-gray-200 rounded py-2 px-4 "
      placeholder="Search ..."
      value={currentRefinement}
      onChange={(event) => refine(event.currentTarget.value)}
    />
  );
};

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
    <li>
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
    <div className="bg-white shadow overflow-hidden sm:rounded-md">
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
    // @ts-ignore:
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
      <div className="relative" ref={ref}>
        <CustomSearchBox
          // @ts-ignore:
          setFocus={setFocus}
        />{' '}
        {focus && (
          <div className={`top-12 w-full absolute`}>
            <CustomHits />
          </div>
        )}
      </div>
    </InstantSearch>
  );
};

const Header = () => (
  <div className="bg-white border-b border-gray-200 fixed top-0 inset-x-0 z-10 h-16 ">
    <div className="max-w-7xl mx-auto sm:px-6 lg:px-8 h-full ">
      <div className="flex items-center h-full">
        <div className="w-1/4 font-bold flex items-center">
          <img
            src="https://images.squarespace-cdn.com/content/v1/5cb5f5d490f904864e26772f/1555429309832-T9W4RY8LN0YOG2WSKHG7/ke17ZwdGBToddI8pDm48kAVes4PdedRJbHzbyrt9K4RZw-zPPgdn4jUwVcJE1ZvWEtT5uBSRWt4vQZAgTJucoTqqXjS3CfNDSuuf31e0tVHE-hDbU1-lN9X0kRdwCihrUiHQfJsM_k09tUzDxHZfTWQ6l2WM7tn7mqHTODzkmeM/44878798-b6e17e00-ac5c-11e8-8d25-2e47e5a53418.png?format=750w"
            width={26}
            className="mr-2"
          />
          <div className="uppercase">Dagster</div>
        </div>
        <div className={`w-3/4 pl-16 pr-4`}>
          <Search />
        </div>
      </div>
    </div>
  </div>
);

export default Header;
