import { parse } from "flatted";
import { useStaticQuery, graphql } from "gatsby";

import { renderElements as defaultRenderElements } from "./components/Element";

export const getBodyNodes = (nodes: NodeListOf<ChildNode>): any => {
  if (nodes === undefined) {
    return [];
  }
  const nodeList = Array.from(nodes);
  return nodeList.reduce((obj, node) => {
    // eslint-disable-next-line @typescript-eslint/ban-ts-ignore
    //@ts-ignore
    if (node.tagName === "body") return node.childNodes;
    return getBodyNodes(node.childNodes);
  }, {});
};

export const ReactParser = ({
  tree: stringifiedTree,
  renderElements = defaultRenderElements
}: any) => {
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
              original {
                src
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
