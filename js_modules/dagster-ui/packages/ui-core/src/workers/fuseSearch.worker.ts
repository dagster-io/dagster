/**
 * A Web Worker that creates and queries a Fuse object.
 */

import {Fuse} from '../search/fuse';

let fuseObject: null | Fuse<any> = null;
let allResults: any = null;

self.addEventListener('message', (event) => {
  const {data} = event;

  switch (data.type) {
    case 'set-results': {
      if (!fuseObject) {
        fuseObject = new Fuse(data.results, data.fuseOptions);
      } else {
        fuseObject.setCollection(data.results);
      }
      allResults = data.results.map(fakeFuseItem);
      self.postMessage({type: 'ready'});
      break;
    }
    case 'query': {
      if (fuseObject) {
        const {queryString} = data;
        const results = queryString ? fuseObject.search(queryString) : allResults;
        self.postMessage({type: 'results', queryString, results});
      }
    }
  }
});

function fakeFuseItem<T>(item: T, refIndex: number = 0): Fuse.FuseResult<T> {
  return {
    item,
    refIndex,
  };
}
