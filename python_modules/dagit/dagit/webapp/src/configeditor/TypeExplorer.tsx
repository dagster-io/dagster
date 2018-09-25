import * as React from "react";
import gql from "graphql-tag";
import { TypeExplorerFragment } from "./types/TypeExplorerFragment";

interface ITypeExplorerProps {
  type: TypeExplorerFragment;
}

export default class TypeExplorer extends React.Component<
  ITypeExplorerProps,
  {}
> {
  static fragments = {
    TypeExplorerFragment: gql`
      fragment TypeExplorerFragment on Type {
        name
        description
      }
    `
  };
  render() {
    return <div>{this.props.type.name}</div>;
  }
}
