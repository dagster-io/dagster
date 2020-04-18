export type AnchorHeading = {
  title?: string;
  href: string;
  element?: 'h1'| 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
};

export type State = {
  anchors: Record<string, AnchorHeading>;
};
export type Action = {
  type: 'ADD_ANCHOR' | 'REMOVE_ANCHOR' | 'RESET';
  payload?: AnchorHeading;
};

export const initialState: State = {
  anchors: {},
};

const reducer = (state: State, { type, payload }: Action): State => {
  switch (type) {
    case 'ADD_ANCHOR':
      return {
        ...state,
        anchors: {
          ...state.anchors,
          [payload!.href]: payload!,
        },
      };
    case 'REMOVE_ANCHOR':
      const { [payload!.href]: excluded, ...newAnchors } = state.anchors;
      return { ...state, anchors: newAnchors };
    case 'RESET':
      return initialState;
  }
};

export default reducer;
