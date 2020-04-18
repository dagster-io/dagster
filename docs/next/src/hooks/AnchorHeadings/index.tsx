import React, {
  createContext,
  useReducer,
  useContext,
  useCallback,
} from 'react';
import reducer, { State, Action, AnchorHeading, initialState } from './reducer';

const AnchorHeadingsDispatchContext = createContext<React.Dispatch<
  Action
> | null>(null);
const AnchorHeadingsContext = createContext<State>(initialState);

export const AnchorHeadingsProvider: React.FC = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);
  return (
    <AnchorHeadingsDispatchContext.Provider value={dispatch}>
      <AnchorHeadingsContext.Provider value={state}>
        {children}
      </AnchorHeadingsContext.Provider>
    </AnchorHeadingsDispatchContext.Provider>
  );
};

export const useAnchorHeadingsActions = () => {
  const dispatch = useContext(AnchorHeadingsDispatchContext);

  const addAnchorHeading = useCallback(
    (heading: AnchorHeading) => {
      if (!dispatch)
        throw new Error(
          'Dispatch has not been initialized (Did you set up AnchorHeadingsProvider ?)',
        );
      dispatch({
        type: 'ADD_ANCHOR',
        payload: heading,
      });
    },
    [dispatch],
  );

  const removeAnchorHeading = useCallback(
    (heading: AnchorHeading) => {
      if (!dispatch)
        throw new Error(
          'Dispatch has not been initialized (Did you set up AnchorHeadingsProvider ?)',
        );
      dispatch({
        type: 'REMOVE_ANCHOR',
        payload: heading,
      });
    },
    [dispatch],
  );

  const clearAnchorHeadings = useCallback(() => {
    if (!dispatch)
      throw new Error(
        'Dispatch has not been initialized (Did you set up AnchorHeadingsProvider ?)',
      );
    dispatch({
      type: 'RESET',
    });
  }, [dispatch]);

  return {
    addAnchorHeading,
    removeAnchorHeading,
    clearAnchorHeadings,
  };
};

export const useAnchorHeadings = () => useContext(AnchorHeadingsContext);
