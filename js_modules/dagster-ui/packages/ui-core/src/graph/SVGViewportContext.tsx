import React, {Dispatch, SetStateAction, createContext, useContext, useMemo, useState} from 'react';

import {DETAIL_ZOOM} from './SVGConsts';
import {usePartialSetStateUpdateCallback} from '../hooks/useSetStateUpdateCallback';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

interface SVGViewportState {
  x: number;
  y: number;
  scale: number;
  minScale: number;
  isClickHeld: boolean;
  isExporting: boolean;
}

interface SVGViewportContextType {
  viewportState: SVGViewportState;
  viewportStateRef: {readonly current: SVGViewportState};
  setViewportState: Dispatch<SetStateAction<SVGViewportState>>;
  mergeViewportState: ReturnType<typeof usePartialSetStateUpdateCallback<SVGViewportState>>[1];
}

const SVGViewportContext = createContext<SVGViewportContextType | null>(null);

export const SVGViewportProvider = ({children}: {children: React.ReactNode}) => {
  const [defaultZoom, setDefaultZoom] = useStateWithStorage('defaultZoom', (value) => {
    if (typeof value !== 'number') {
      return DETAIL_ZOOM;
    }
    return value;
  });

  const [viewportState, setViewportState] = useState<SVGViewportState>({
    x: 0,
    y: 0,
    scale: defaultZoom,
    minScale: 0,
    isClickHeld: false,
    isExporting: false,
  });

  const [viewportStateRef, mergeViewportState] = usePartialSetStateUpdateCallback(
    viewportState,
    (partial) => {
      if (partial.scale !== undefined) {
        // Update the default zoom to whatever the user last set the zoom to
        setDefaultZoom(partial.scale);
      }
      setViewportState((prev) => ({...prev, ...partial}));
    },
  );

  const context = useMemo(
    () => ({viewportState, viewportStateRef, setViewportState, mergeViewportState}),
    [viewportState, viewportStateRef, setViewportState, mergeViewportState],
  );
  const wrappingContext = useContext(SVGViewportContext);

  return (
    <SVGViewportContext.Provider value={wrappingContext ?? context}>
      {children}
    </SVGViewportContext.Provider>
  );
};

export const useSVGViewport = () => {
  const context = useContext(SVGViewportContext);
  if (!context) {
    throw new Error('useSVGViewport must be used within SVGViewportProvider');
  }
  return context;
};
