/**
 * A Web Worker that creates and queries a Fuse object.
 */

import {createWorkerThread} from 'shared/workers/WorkerThread.oss';

import {Fuse} from '../search/fuse';

let fuseObject: null | Fuse<any> = null;
let allResults: any = null;

createWorkerThread(
  async (postMessage: (message: any) => void, data: any) => {
    switch (data.type) {
      case 'set-results': {
        if (!fuseObject) {
          fuseObject = new Fuse(data.results, data.fuseOptions);
        } else {
          fuseObject.setCollection(data.results);
        }
        allResults = data.results.map(fakeFuseItem);
        postMessage({type: 'ready'});
        break;
      }
      case 'query': {
        if (fuseObject) {
          const {queryString} = data;
          const results = queryString ? fuseObject.search(queryString) : allResults;
          postMessage({type: 'results', queryString, results});
        }
        break;
      }
    }
  },
  (_postMessage: (message: any) => void, error: Error) => {
    console.error(error);
  },
);

function fakeFuseItem<T>(item: T, refIndex: number = 0): Fuse.FuseResult<T> {
  return {
    item,
    refIndex,
  };
}
