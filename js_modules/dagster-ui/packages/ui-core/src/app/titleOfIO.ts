export const DEFAULT_RESULT_NAME = 'result';

export const titleOfIO = (i: {solid: {name: string}; definition: {name: string}}) => {
  return i.solid.name !== DEFAULT_RESULT_NAME
    ? `${i.solid.name}:${i.definition.name}`
    : i.solid.name;
};
