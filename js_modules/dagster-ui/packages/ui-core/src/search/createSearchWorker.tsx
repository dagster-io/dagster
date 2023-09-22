import Fuse from 'fuse.js';
import memoize from 'lodash/memoize';

import {ResultResponse, SearchResult} from './types';

const spawnSearchWorker = memoize(
  (_key: string) => new Worker(new URL('../workers/fuseSearch.worker', import.meta.url)),
);

type QueryListener = {
  queryString: string;
  listener: (response: QueryResponse) => void;
};

type QueryResponse = {queryString: string; results: Fuse.FuseResult<SearchResult>[]};

export type WorkerSearchResult = {
  update: (results: SearchResult[]) => void;
  search: (queryString: string) => Promise<QueryResponse>;
  terminate: () => void;
};

/**
 * Create a queryable search worker.
 *
 * @param key - Unique identifier for the memoized Web Worker
 * @param fuseOptions - Options to pass to the Fuse constructor
 */
export const createSearchWorker = (
  key: string,
  fuseOptions: Fuse.IFuseOptions<SearchResult>,
): WorkerSearchResult => {
  const searchWorker = spawnSearchWorker(key);
  const listeners: Set<QueryListener> = new Set();

  searchWorker.addEventListener('message', (event) => {
    const {data} = event;
    if (data.type === 'results') {
      const {queryString, results} = data as ResultResponse;

      // Inform listeners for this querystring. Remove them after they're done.
      for (const listener of listeners) {
        if (listener.queryString === queryString) {
          listener.listener({queryString, results});
          listeners.delete(listener);
        }
      }
    }
  });

  /**
   * Set the results for the worker, either for initialization or to update them.
   *
   * @param results - Prepackaged search results, supplied via GraphQL or otherwise
   */
  const update = (results: SearchResult[]) => {
    searchWorker.postMessage({type: 'set-results', results, fuseOptions});
  };

  /**
   * Perform a search on the worker. Resolves with the list of matching results.
   *
   * @param queryString
   */
  const search = async (queryString: string): Promise<QueryResponse> => {
    return new Promise((resolve) => {
      listeners.add({
        queryString,
        listener: (response) => resolve(response),
      });

      // Query worker for results.
      searchWorker.postMessage({type: 'query', queryString});
    });
  };

  const terminate = () => searchWorker.terminate();

  return {update, search, terminate};
};
