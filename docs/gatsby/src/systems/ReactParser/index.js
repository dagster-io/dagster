import { parse } from "flatted";
import { useStaticQuery, graphql } from "gatsby";

import { renderElements as defaultRenderElements } from "./components/Element";
import { string } from "prop-types";

export const getBodyNodes = nodes => {
  if (nodes === undefined) {
    return [];
  }

  return nodes.reduce((obj, node) => {
    if (node.tagName === "body") return node.childNodes;
    return getBodyNodes(node.childNodes);
  }, {});
};

export const ReactParser = ({
  tree: stringifiedTree,
  renderElements = defaultRenderElements
}) => {
  const data = useStaticQuery(graphql`
    query AllImages {
      allFile(filter: { ext: { regex: "/.(png|jpeg)/" } }) {
        edges {
          node {
            absolutePath
            childImageSharp {
              fluid(maxWidth: 1024) {
                ...GatsbyImageSharpFluid_noBase64
              }
            }
          }
        }
      }
    }
  `);

  if (stringifiedTree === null) {
    return [];
  }

  const tree = parse(stringifiedTree);
  const bodyNodes = getBodyNodes(tree.childNodes);

  return bodyNodes.reduce(renderElements(data.allFile.edges), []);
};

export * from "./components/Element";
