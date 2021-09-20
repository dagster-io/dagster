import React from 'react';

type PipelineExplorerJobContextData =
  | {
      sidebarTab: React.ReactNode;
    }
  | false;

export const PipelineExplorerJobContext = React.createContext<PipelineExplorerJobContextData>(
  false,
);
