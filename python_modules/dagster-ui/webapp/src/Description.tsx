import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { H1, H2, H3, H4, H5, H6, Text, Code, UL, Pre } from "@blueprintjs/core";
import * as ReactMarkdown from "react-markdown";

interface IDescriptionProps {
  description: string | null;
}

const MARKDOWN_RENDERERS: ReactMarkdown.Renderers = {
  list: ({ children }) => <UL>{children}</UL>,
  heading: ({
    level,
    children
  }: {
    level: number;
    children: React.ReactNode;
  }) => {
    switch (level) {
      case 1:
        return <H1>{children}</H1>;
      case 2:
        return <H2>{children}</H2>;
      case 3:
        return <H3>{children}</H3>;

      case 4:
        return <H4>{children}</H4>;

      case 5:
        return <H5>{children}</H5>;
      case 6:
        return <H6>{children}</H6>;
      default:
        return <H6>{children}</H6>;
    }
  },
  inlineCode: ({ children }) => <Code>{children}</Code>,
  code: ({ children }) => <Pre>{children}</Pre>
};

export default class Description extends React.Component<
  IDescriptionProps,
  {}
> {
  render() {
    if (!this.props.description || this.props.description.length === 0) {
      return null;
    } else {
      return (
        <ReactMarkdown
          source={this.props.description}
          renderers={MARKDOWN_RENDERERS}
        />
      );
    }
  }
}
