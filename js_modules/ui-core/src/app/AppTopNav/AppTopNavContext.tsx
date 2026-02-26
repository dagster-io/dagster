import {useCallback, useLayoutEffect} from 'react';
import {atom, useRecoilState, useRecoilValue, useSetRecoilState} from 'recoil';

export const isFullScreenAtom = atom<boolean>({
  key: 'isFullScreenAtom',
  default: false,
});

export const isFullScreenAllowedAtom = atom<boolean>({
  key: 'isFullScreenAllowedAtom',
  default: false,
});

export const useFullScreen = () => {
  // FullScreen causes the navigation to be hidden to create more room.
  const [isFullScreen, setIsFullScreen] = useRecoilState(isFullScreenAtom);

  // Not every page supports full screen mode, a page can use the useFullScreenAllowedView hook to enable it.
  const isFullScreenAllowed = useRecoilValue(isFullScreenAllowedAtom);

  return {
    isFullScreen: isFullScreen && isFullScreenAllowed,
    setIsFullScreen,
    toggleFullScreen: useCallback(
      () => setIsFullScreen((isFullScreen) => !isFullScreen),
      [setIsFullScreen],
    ),
  };
};

export const useFullScreenAllowedView = () => {
  const setIsFullScreenAllowed = useSetRecoilState(isFullScreenAllowedAtom);
  useLayoutEffect(() => {
    setIsFullScreenAllowed(true);
    return () => setIsFullScreenAllowed(false);
  }, [setIsFullScreenAllowed]);
};
