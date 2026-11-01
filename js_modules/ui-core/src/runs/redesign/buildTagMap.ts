export const buildTagMap = (tags: {key: string; value: string}[]) =>
  new Map(tags.map(({key, value}) => [key, value]));
