import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { H1, H2, H3, H4, H5, H6, Text, Code, UL, Pre } from "@blueprintjs/core";
import * as ReactMarkdown from "react-markdown";

interface IDescriptionProps {
  description: string | null;
}

export default class Description extends React.Component<
  IDescriptionProps,
  {}
> {
  render() {
    if (!this.props.description || this.props.description.length === 0) {
      return null;
    } else {
      return <ReactMarkdown source={this.props.description} />;
    }
  }
}
