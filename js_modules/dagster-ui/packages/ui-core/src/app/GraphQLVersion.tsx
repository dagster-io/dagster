import {useEffect} from 'react';
import {useHistory} from 'react-router-dom';
import {atom, selector, useRecoilState} from 'recoil';

export const graphQLVersionAtom = atom<string | undefined>({
  key: 'graphQLVersionAtom',
  default: undefined,
});

export const initialGraphQLVersionAtom = atom<string | undefined>({
  key: 'initialGraphQLVersionAtom',
  default: undefined,
});

export const initialGraphQLVersionOnceAtom = selector<string | undefined>({
  key: 'initialGraphQLVersionOnceAtom',
  get: ({get}) => get(initialGraphQLVersionAtom),
  set: ({get, set}, newValue) => {
    const current = get(initialGraphQLVersionAtom);
    if (!current && typeof newValue === 'string') {
      set(initialGraphQLVersionAtom, newValue);
    }
  },
});

export function ReloadOnHistoryChangeIfNewVersionAvailable() {
  const [latestVersion] = useRecoilState(graphQLVersionAtom);
  const [initialVersion] = useRecoilState(initialGraphQLVersionAtom);
  const versionChanged = latestVersion && initialVersion && latestVersion !== initialVersion;

  const history = useHistory();

  useEffect(() => {
    const unlisten = history.listen((_location, action) => {
      if (action === 'POP') {
        return; // Browser "Back" action
      }
      if (versionChanged) {
        window.location.reload();
      }
    });
    return unlisten;
  }, [history, versionChanged]);

  return null;
}
