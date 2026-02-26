import {ReactNode} from 'react';

export type NavigationItem = {
  key: string;
  label: string;
  element: ReactNode;
  shortcut?: {
    filter: (event: KeyboardEvent) => boolean;
    label: string;
    path: string;
  };
  right?: ReactNode;
};

export type NavigationGroup = {
  key: string;
  items: (NavigationItem | null)[];
};
