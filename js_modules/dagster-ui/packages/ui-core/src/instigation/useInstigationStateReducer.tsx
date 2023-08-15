import React from 'react';

export type OpenWithIntent = 'not-open' | 'start' | 'stop';

type CompletionState = {completed: number; errors: {[id: string]: string}};

type DialogState = {
  step: 'initial' | 'updating' | 'completed';
  completion: CompletionState;
};

type DialogAction =
  | {type: 'reset'}
  | {type: 'start'}
  | {type: 'update-success'}
  | {type: 'update-error'; name: string; error: string}
  | {type: 'complete'};

const initialState: DialogState = {
  step: 'initial',
  completion: {completed: 0, errors: {}},
};

const reducer = (prevState: DialogState, action: DialogAction): DialogState => {
  switch (action.type) {
    case 'reset':
      return initialState;
    case 'start':
      return {...prevState, step: 'updating'};
    case 'update-success': {
      const {completion} = prevState;
      return {
        step: 'updating',
        completion: {...completion, completed: completion.completed + 1},
      };
    }
    case 'update-error': {
      const {completion} = prevState;
      return {
        step: 'updating',
        completion: {
          ...completion,
          completed: completion.completed + 1,
          errors: {...completion.errors, [action.name]: action.error},
        },
      };
    }
    case 'complete':
      return {...prevState, step: 'completed'};
  }
};

export const useInstigationStateReducer = () => React.useReducer(reducer, initialState);
