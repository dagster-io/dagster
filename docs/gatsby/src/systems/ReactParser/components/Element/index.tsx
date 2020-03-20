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

/**
 * TODO: Lower "Any" usage here.
 */

export const isText = ({ nodeName }: { nodeName: string }) => {
  return nodeName === "#text";
};

const isHeading = (tag: string) => {
  return ["h1", "h2", "h3", "h4", "h5", "h5"].indexOf(tag) !== -1;
};

// TODO: Add typings to this. I don't really understand
// why does ramda return unknown by default
const getLanguage = (node: any) => {
  const attrs = R.path<any>(["parentNode", "parentNode", "attrs"], node);
  const classes =
    attrs &&
    attrs.length > 0 &&
    attrs.find(
      (attr: any) =>
        attr && attr.name === "class" && attr.value.includes("highlight-")
    );

  const language = classes && classes.value.match(/highlight\-(\w+)/);
  return language && language[1];
};

const isSphinxHeading = (
  Component: string | Function | JSX.Element,
  props: { className: string }
) => {
  return Component === "p" && props.className && props.className === "rubric";
};

const isSphinxLineNumbers = (
  Component: string | Function | JSX.Element,
  props: { className: string }
) => {
  return Component === "td" && props.className && props.className === "linenos";
};

// TODO: Let's find a proper type for this.
const isCode = (Component: any) => {
  return Component && Component.tagName === "code";
};

const isImageLink = (
  _node: any,
  props: { className: string; href: string }
) => {
  return props.className === "permalink" && props.href.includes("/_images");
};

// TODO: Let's check this later.
export const renderElements = (images: any[]) => (
  renderedElements: any,
  node: any,
  idx: number
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

export const Element: any = (node: HTMLInputElement & { images: any[] }) => {
  const { tagName: Component, nodeName, childNodes, value, images = [] } = node;
  const { props, children } = useElement(node as any, renderElements);

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

  if (isSphinxHeading(Component, props as any)) {
    return (
      <Heading tagName="h3" {...props}>
        {children}
      </Heading>
    );
  }

  if (isSphinxLineNumbers(Component, props as any)) {
    props.style.width = "1%";
  }

  if (Component === "div" && props.id && props.id.startsWith("id")) {
    return <CodeSection {...props} nodes={childNodes as any} />;
  }

  if (Component === "hr") {
    return <hr {...props} />;
  }

  if (isImageLink(node, props as any)) {
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

  // TODO: This intrinsic-attributes error is going to be fun to fix
  // eslint-disable-next-line @typescript-eslint/ban-ts-ignore
  // @ts-ignore
  return <Component {...props}>{children}</Component>;
};
