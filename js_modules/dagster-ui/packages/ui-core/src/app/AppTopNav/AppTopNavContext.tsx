import {useLocation} from 'react-router-dom';
import {atom} from 'recoil';

export const isFullScreenAtom = atom<boolean>({
  key: 'isFullScreenAtom',
  default: false,
});

export const canForceFullScreen = (location: ReturnType<typeof useLocation>): boolean => {
  const {pathname, search} = location;
  const searchParams = new URLSearchParams(search);
  return pathname.startsWith('/selection/') && searchParams.get('selectedTab') === 'lineage';
};
