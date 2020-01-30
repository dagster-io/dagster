/** @jsx jsx */
import { jsx } from "theme-ui";
import styleToObj from "style-to-object";

import {
  Code,
  Details,
  Image,
  Link,
  List,
  Heading,
  Table,
  CodeSection,
  Pre
} from "systems/Core";

import { useElement } from "../../hooks/useElement";

export const isText = ({ nodeName }) => {
  return nodeName === "#text";
};

const isHeading = tag => {
  return ["h1", "h2", "h3", "h4", "h5", "h5"].indexOf(tag) !== -1;
};

const isSphinxHeading = (Component, props) => {
  return Component === "p" && props.className && props.className === "rubric";
};

const isCode = (Component, props) => {
  return Component && Component.tagName === "code";
};

export const renderElements = images => (
  renderedElements,
  node,
  idx,
  _nodes
) => {
  if (isText(node)) {
    renderedElements.push(node.value);
  } else if (
    isCode(node) &&
    renderedElements.length > 0 &&
    isCode(renderedElements[-1]) //&&
  ) {
    renderedElements[-1].children =
      renderedElements[-1].children + node.children;
  } else {
    renderedElements.push(
      <Element key={node.nodeName + idx} {...node} images={images} />
    );
  }
  return renderedElements;
};

export const Element = node => {
  const { tagName: Component, nodeName, childNodes, value, images = [] } = node;
  const { props, children } = useElement(node, renderElements);

  if (props.style && typeof props.style == "string") {
    props.style = styleToObj(props.style);
  }

  if (nodeName === "#text") {
    return value;
  }

  if (!Component) {
    return null;
  }

  if (isSphinxHeading(Component, props)) {
    return (
      <Heading tagName="h3" {...props}>
        {children}
      </Heading>
    );
  }

  if (Component === "div" && props.id && props.id.startsWith("id")) {
    return <CodeSection {...props} nodes={childNodes} />;
  }

  if (Component === "hr") {
    return <hr {...props} />;
  }

  if (Component === "a") {
    return <Link {...props}>{children}</Link>;
  }

  if (Component === "table") {
    return <Table {...props}>{children}</Table>;
  }

  if (Component === "img") {
    return <Image {...props} images={images} />;
  }

  if (isCode(Component)) {
    return <Code {...props}>{children}</Code>;
  }

  if (Component === "li") {
    return <List {...props}>{children}</List>;
  }

  if (
    Component === "dl" &&
    props.className &&
    ["function", "class", "data"].some(v => props.className.includes(v))
  ) {
    return <Details {...props}>{children}</Details>;
  }

  if (Component === "pre") {
    return <Pre {...props}>{children}</Pre>;
  }

  if (isHeading(Component)) {
    return (
      <Heading {...props} tagName={Component}>
        {children}
      </Heading>
    );
  }

  return <Component {...props}>{children}</Component>;
};
