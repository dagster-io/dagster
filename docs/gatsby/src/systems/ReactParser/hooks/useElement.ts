import { useMemo } from "react";
import camelize from "camelize";
import { TraverseNode } from "systems/Core/CodeSection";

const reduceProps = (attrs: Record<string, any>): Record<string, any> =>
  attrs
    ? attrs.reduce(
        (
          obj: Record<string, any>,
          { name, value }: { name: string; value: any }
        ) => {
          if (name === "class") name = "className";
          if (!name.startsWith("data-")) name = camelize(name);
          return { ...obj, [name]: value };
        },
        {}
      )
    : {};

export function useElement(
  node: TraverseNode & { images: any[] },
  renderElements: (inputs: any) => any
) {
  const { childNodes, attrs, images = [] } = node;

  const props = useMemo(() => reduceProps(attrs), [attrs]);
  const children =
    childNodes && Array.from(childNodes).reduce(renderElements(images), []);

  return {
    props,
    children
  };
}
