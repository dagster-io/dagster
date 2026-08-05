import {useContext, useMemo} from 'react';

import {DefinitionsSource} from '../../graphql/types';
import {WorkspaceContext} from '../../workspace/WorkspaceContext/WorkspaceContext';

export function useConnectionLocationNames(): Set<string> {
  const {locationEntries} = useContext(WorkspaceContext);

  return useMemo(() => {
    const names = new Set<string>();
    for (const entry of locationEntries) {
      if (entry.definitionsSource === DefinitionsSource.CONNECTION) {
        names.add(entry.name);
      }
    }
    return names;
  }, [locationEntries]);
}
