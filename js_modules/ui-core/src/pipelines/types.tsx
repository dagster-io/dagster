import {ReactNode} from 'react';

export type TabKey = 'types' | 'info' | 'alerts';

export interface TabDefinition {
  name: string;
  key: TabKey;
  content: () => ReactNode;
}
