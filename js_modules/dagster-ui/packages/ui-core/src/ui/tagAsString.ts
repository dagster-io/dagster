export const buildTagString = ({key, value}: {key: string; value: string}) => {
  if (value === '') {
    return key;
  }
  return `${key}: ${value}`;
};
