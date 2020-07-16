import { Component } from 'react';

class DocSearch extends Component<{}> {
  componentDidMount() {
    // @ts-ignore
    if (window.docsearch) {
      // @ts-ignore
      window.docsearch({
        apiKey: '991c27897aafec73e6eff85912eed810',
        indexName: 'fulltext',
        appId: 'CTO1CV9T4R',
        inputSelector: '#algolia-doc-search',
      });
    }
  }

  render() {
    return (
      <div className="relative flex-1 flex items-center justify-center px-2 lg:ml-6 lg:justify-end">
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
              id="algolia-doc-search"
              className="block w-full pl-2 pr-2 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:border-blue-300 focus:shadow-outline-blue sm:text-sm transition duration-150 ease-in-out"
              placeholder="Search Docs"
              type="search"
            />
          </div>
        </div>
      </div>
    );
  }
}

export default DocSearch;
