import {MutableRefObject, useEffect} from 'react';

import {SVGViewport} from '../graph/SVGViewport';
import {getJSONForKey} from '../hooks/useStateWithStorage';

const LINEAGE_GRAPH_ZOOM_LEVEL = 'lineageGraphZoomLevel';

export const SVGSaveZoomLevel = ({scale}: {scale: number}) => {
  useEffect(() => {
    try {
      window.localStorage.setItem(LINEAGE_GRAPH_ZOOM_LEVEL, JSON.stringify(scale));
    } catch (err) {
      // no-op
    }
  }, [scale]);
  return <></>;
};

export function useLastSavedZoomLevel(
  viewportEl: MutableRefObject<SVGViewport | undefined>,
  layout: import('../asset-graph/layout').AssetGraphLayout | null,
  graphFocusChangeKey: string,
) {
  useEffect(() => {
    if (viewportEl.current && layout) {
      const lastZoomLevel = Number(getJSONForKey(LINEAGE_GRAPH_ZOOM_LEVEL));
      viewportEl.current.autocenter(false, lastZoomLevel);
      viewportEl.current.focus();
    }
  }, [viewportEl, layout, graphFocusChangeKey]);
}
