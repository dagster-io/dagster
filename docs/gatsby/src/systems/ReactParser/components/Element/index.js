/** @jsx jsx */
import * as R from "ramda";
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

const getLanguage = node => {
  const attrs = R.path(["parentNode", "parentNode", "attrs"], node);
  const classes =
    attrs &&
    attrs.length > 0 &&
    attrs.find(
      attr => attr && attr.name === "class" && attr.value.includes("highlight-")
    );

  const language = classes && classes.value.match(/highlight\-(\w+)/);
  return language && language[1];
};

const isSphinxHeading = (Component, props) => {
  return Component === "p" && props.className && props.className === "rubric";
};

const isSphinxLineNumbers = (Component, props) => {
  return Component === "td" && props.className && props.className === "linenos";
};

const isCode = (Component, _props) => {
  return Component && Component.tagName === "code";
};

const isImageLink = (node, props) => {
  return props.className === "permalink" && props.href.includes("/_images");
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
  } else {
    props.style = {};
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

  if (isSphinxLineNumbers(Component, props)) {
    props.style.width = "1%";
  }

  if (Component === "div" && props.id && props.id.startsWith("id")) {
    return <CodeSection {...props} nodes={childNodes} />;
  }

  if (Component === "hr") {
    return <hr {...props} />;
  }

  if (isImageLink(node, props)) {
    return children;
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
    return (
      <Pre {...props} data-language={getLanguage(node)}>
        {children}
      </Pre>
    );
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
