/** @jsx jsx */
import { jsx } from "theme-ui";
import { produce } from "immer";
import traverse from "parse5-traverse";

import * as styles from "./styles";
import { renderElements } from "systems/ReactParser";
import { DetailedHTMLProps, HTMLAttributes } from "react";

export type TraverseNode = HTMLElement & {
  attrs: any[];
  value: any;
};

const findPreInTree = (node: TraverseNode, language: string) => {
  const acc: TraverseNode[] = [];
  traverse(node, {
    post(node: TraverseNode, parent: TraverseNode) {
      if (node.tagName === "pre" && parent.tagName === "div") {
        node.attrs.push({ name: "data-language", value: language });
        acc.push(node);
      }
    }
  });

  return acc;
};

const findLanguage = (node: TraverseNode) => {
  let language = "";
  traverse(node, {
    post(node: TraverseNode) {
      const regexp = /(.+)(\.)(.+)$/;
      if (node.nodeName === "#text" && regexp.test(node.value)) {
        language = node.value.match(regexp)[3];
      }
    }
  });
  return language;
};

const removeTableElements = (language: string) => (node: TraverseNode) => {
  if (node.attrs.length > 0 && node.attrs[0].value === "code-block") {
    return { ...node, childNodes: findPreInTree(node, language) };
  }
  return node;
};

const parseChildren = (nodes: TraverseNode[]) => {
  const child = nodes.filter(({ nodeName }) => nodeName !== "#text");
  return produce(child, draft => {
    draft[0].attrs.push({ name: "className", value: "code-file" });
    draft[1].attrs.push({ name: "className", value: "code-block" });
  });
};

type CodeSectionProps = DetailedHTMLProps<
  HTMLAttributes<HTMLElement>,
  HTMLElement
> & {
  nodes: TraverseNode[];
};

export const CodeSection: React.FC<CodeSectionProps> = ({
  nodes,
  ...props
}) => {
  const children = parseChildren(nodes);
  const language = findLanguage(children[0]);

  return (
    <section {...props} sx={styles.wrapper}>
      {children
        .map(removeTableElements(language))
        .reduce(renderElements([]), [])}
    </section>
  );
};
