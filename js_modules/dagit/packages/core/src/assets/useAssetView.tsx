import * as React from 'react';

const ASSET_VIEW_KEY = 'AssetViewPreference';

export type View = 'flat' | 'directory';

type Output = [View, (update: View) => void];

export const useAssetView = () => {
  const [view, setView] = React.useState<View>(() => {
    const storedValue = window.localStorage.getItem(ASSET_VIEW_KEY);
    if (storedValue === 'flat' || storedValue === 'directory') {
      return storedValue;
    }
    return 'flat';
  });

  const onChange = React.useCallback((update: View) => {
    window.localStorage.setItem(ASSET_VIEW_KEY, update);
    setView(update);
  }, []);

  return React.useMemo(() => [view, onChange], [view, onChange]) as Output;
};
