export type TreeLink = {
  name: string;
  path: string;
  children?: TreeLink[];
  childPath?: boolean[];
  isExternal?: boolean;
  ignore?: boolean;
};

export const flatten = (items: TreeLink[], includeTopItem: boolean = false) => {
  const flat: TreeLink[] = [];
  items.forEach((item) => {
    if (Array.isArray(item.children)) {
      if (includeTopItem) flat.push(item);
      flat.push(...flatten(item.children));
    } else {
      flat.push(item);
    }
  });
  return flat;
};
