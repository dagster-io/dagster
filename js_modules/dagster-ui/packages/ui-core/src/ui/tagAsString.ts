const TAG_NO_VALUE_SENTINEL = '__dagster_no_value';

export const buildTagString = ({key, value}: {key: string; value: string}) => {
  if (value === TAG_NO_VALUE_SENTINEL) {
    return key;
  }
  return `${key}: ${value}`;
};
