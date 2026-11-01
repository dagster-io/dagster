import {ReactNode, useState} from 'react';

import {LayoutMode, LayoutModeContext, detectLayoutMode} from './LayoutMode';

interface Props {
  // Force a mode (stories, tests). Otherwise detected once at mount.
  mode?: LayoutMode;
  children: ReactNode;
}

export const LayoutModeProvider = ({mode, children}: Props) => {
  const [detected] = useState(detectLayoutMode);
  return (
    <LayoutModeContext.Provider value={mode ?? detected}>{children}</LayoutModeContext.Provider>
  );
};
