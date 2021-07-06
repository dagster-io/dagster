import React from 'react';

export type PipelineExplorerJobContextData =
  | {
      sidebarTab: React.ReactNode;
    }
  | false;

export const PipelineExplorerJobContext = React.createContext<PipelineExplorerJobContextData>(
  false,
);
