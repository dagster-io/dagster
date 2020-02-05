/** @jsx jsx */
import { jsx } from "theme-ui";
import { produce } from "immer";
import traverse from "parse5-traverse";

import * as styles from "./styles";
import { renderElements } from "systems/ReactParser";

const findPreInTree = (node, language) => {
  const acc = [];
  traverse(node, {
    post(node, parent) {
      if (node.tagName === "pre" && parent.tagName === "div") {
        node.attrs.push({ name: "data-language", value: language });
        acc.push(node);
      }
    }
  });

  return acc;
};

const findLanguage = node => {
  let language = "";
  traverse(node, {
    post(node) {
      const regexp = /(.+)(\.)(.+)$/;
      if (node.nodeName === "#text" && regexp.test(node.value)) {
        language = node.value.match(regexp)[3];
      }
    }
  });
  return language;
};

const removeTableElements = language => node => {
  if (node.attrs.length > 0 && node.attrs[0].value === "code-block") {
    return { ...node, childNodes: findPreInTree(node, language) };
  }
  return node;
};

const parseChildren = nodes => {
  const child = nodes.filter(({ nodeName }) => nodeName !== "#text");
  return produce(child, draft => {
    draft[0].attrs.push({ name: "className", value: "code-file" });
    draft[1].attrs.push({ name: "className", value: "code-block" });
  });
};

export const CodeSection = ({ nodes, ...props }) => {
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
