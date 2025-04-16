import {atom} from 'recoil';

export const isFullScreenAtom = atom<boolean>({
  key: 'isFullScreenAtom',
  default: false,
});
