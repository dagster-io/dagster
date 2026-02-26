import React from 'react';

let _isSearchVisible = false;
const _listeners: Array<(visible: boolean) => void> = [];

export const useSearchVisibility = () => {
  const [isSearchVisible, setIsSearchVisible] = React.useState(_isSearchVisible);

  React.useEffect(() => {
    _listeners.push(setIsSearchVisible);
    return () => {
      const index = _listeners.indexOf(setIsSearchVisible);
      if (index !== -1) {
        _listeners.splice(index, 1);
      }
    };
  }, []);
  return isSearchVisible;
};

export function __updateSearchVisibility(isVisible: boolean) {
  if (_isSearchVisible !== isVisible) {
    _isSearchVisible = isVisible;
    _listeners.forEach((listener) => {
      listener(_isSearchVisible);
    });
  }
}

export function isSearchVisible() {
  return _isSearchVisible;
}
