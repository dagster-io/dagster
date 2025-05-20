import {useCallback, useLayoutEffect} from 'react';
import {atom, useRecoilState, useSetRecoilState} from 'recoil';

export const isFullScreenAtom = atom<boolean>({
  key: 'isFullScreenAtom',
  default: false,
});

export const isFullScreenAllowedAtom = atom<boolean>({
  key: 'isFullScreenAllowedAtom',
  default: false,
});

export const useFullscreen = () => {
  const [isFullScreen, setIsFullScreen] = useRecoilState(isFullScreenAtom);
  const [isFullScreenEnabled, setIsFullScreenEnabled] = useRecoilState(isFullScreenAllowedAtom);

  return {
    isFullScreen: isFullScreen && isFullScreenEnabled,
    setIsFullScreen,
    setIsFullScreenEnabled,
    toggleFullScreen: useCallback(
      () => setIsFullScreen((isFullScreen) => !isFullScreen),
      [setIsFullScreen],
    ),
  };
};

export const useFullScreenEnabledView = () => {
  const setIsFullScreenEnabled = useSetRecoilState(isFullScreenAllowedAtom);
  useLayoutEffect(() => {
    setIsFullScreenEnabled(true);
    return () => setIsFullScreenEnabled(false);
  }, [setIsFullScreenEnabled]);
};
