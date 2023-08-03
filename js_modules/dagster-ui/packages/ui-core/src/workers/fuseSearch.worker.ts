/**
 * A Web Worker that creates and queries a Fuse object.
 */
let fuseObject: any = null;

self.addEventListener('message', (event) => {
  const {data} = event;

  switch (data.type) {
    case 'set-results': {
      // Before we attempt any imports, manually set the Webpack public path to the static path root.
      // This allows us to import paths when a path-prefix value has been set.
      if (data.staticPathRoot) {
        // @ts-expect-error -- Cannot add annotation to magic webpack var
        __webpack_public_path__ = data.staticPathRoot;
      }

      import('../search/fuse').then(({Fuse}) => {
        if (!fuseObject) {
          fuseObject = new Fuse(data.results, data.fuseOptions);
        } else {
          fuseObject.setCollection(data.results);
        }
        self.postMessage({type: 'ready'});
      });
      break;
    }
    case 'query': {
      if (fuseObject) {
        const {queryString} = data;

        // Consider the empty string as returning no results.
        const results = queryString ? fuseObject.search(queryString) : [];
        self.postMessage({type: 'results', queryString, results});
      }
    }
  }
});
