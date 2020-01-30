import { useMemo } from "react";
import camelize from "camelize";

const reduceProps = attrs =>
  attrs
    ? attrs.reduce((obj, { name, value }) => {
        if (name === "class") name = "className";
        if (!name.startsWith("data-")) name = camelize(name);
        return { ...obj, [name]: value };
      }, {})
    : {};

export function useElement(node, renderElements) {
  const { childNodes, attrs, images = [] } = node;

  const props = useMemo(() => reduceProps(attrs), [attrs]);
  const children = childNodes && childNodes.reduce(renderElements(images), []);

  return {
    props,
    children
  };
}
