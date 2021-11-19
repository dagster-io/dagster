import React from 'react';

// Note: The motivation for this is that the SnapshotRoot shouldn't
// show this tab, and there's not enought context to remove it far down in
// the component tree.
type GraphExplorerJobContextData =
  | {
      sidebarTab: React.ReactNode;
    }
  | false;

export const GraphExplorerJobContext = React.createContext<GraphExplorerJobContextData>(false);
