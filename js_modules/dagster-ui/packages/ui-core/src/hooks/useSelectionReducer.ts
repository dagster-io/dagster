import {useLayoutEffect, useReducer} from 'react';

type State = {
  checkedIds: Set<string>;
  lastCheckedId: string | null;
};

type Action =
  | {type: 'toggle-one'; payload: {checked: boolean; id: string}}
  | {
      type: 'toggle-slice';
      payload: {checked: boolean; id: string; allIds: string[]};
    }
  | {type: 'toggle-all'; payload: {checked: boolean; allIds: string[]}}
  | {type: 'set-all-ids'; payload: {allIds: string[]}};

const reducer = (state: State, action: Action): State => {
  const copy = new Set(state.checkedIds);
  switch (action.type) {
    case 'set-all-ids': {
      const allIdsSet = new Set(action.payload.allIds);
      return {
        checkedIds: new Set(Array.from(state.checkedIds).filter((id) => allIdsSet.has(id))),
        lastCheckedId: state.lastCheckedId,
      };
    }
    case 'toggle-one': {
      const {checked, id} = action.payload;
      if (checked) {
        copy.add(id);
      } else {
        copy.delete(id);
      }
      return {lastCheckedId: id, checkedIds: copy};
    }

    case 'toggle-slice': {
      const {checked, id, allIds} = action.payload;
      const {lastCheckedId} = state;

      const indexOfLast = lastCheckedId ? allIds.indexOf(lastCheckedId) : -1;
      const indexOfChecked = allIds.indexOf(id);
      if (indexOfLast === -1 || indexOfChecked === -1) {
        return state;
      }

      const [start, end] = [indexOfLast, indexOfChecked].sort();
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      allIds.slice(start, end! + 1).forEach((id) => {
        if (checked) {
          copy.add(id);
        } else {
          copy.delete(id);
        }
      });

      return {
        lastCheckedId: id,
        checkedIds: copy,
      };
    }

    case 'toggle-all': {
      const {checked, allIds} = action.payload;
      return {
        lastCheckedId: null,
        checkedIds: checked ? new Set(allIds) : new Set(),
      };
    }
  }
};

const initialState: State = {
  checkedIds: new Set(),
  lastCheckedId: null,
};

export function useSelectionReducer(allIds: string[]) {
  const [state, dispatch] = useReducer(reducer, initialState);

  useLayoutEffect(() => {
    dispatch({type: 'set-all-ids', payload: {allIds}});
  }, [allIds]);

  const onToggleFactory = (id: string) => (values: {checked: boolean; shiftKey: boolean}) => {
    const {checked, shiftKey} = values;
    if (shiftKey && state.lastCheckedId) {
      dispatch({type: 'toggle-slice', payload: {checked, id, allIds}});
    } else {
      dispatch({type: 'toggle-one', payload: {checked, id}});
    }
  };

  const onToggleAll = (checked: boolean) => {
    dispatch({type: 'toggle-all', payload: {checked, allIds}});
  };

  return [state, {onToggleFactory, onToggleAll}] as const;
}
