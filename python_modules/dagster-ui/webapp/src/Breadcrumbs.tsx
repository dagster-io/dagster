import * as React from "react";
import styled from "styled-components";
import { Classes } from "@blueprintjs/core";

interface IBreadcrumbsProps {
  className?: string;
}

export class Breadcrumbs extends React.Component<IBreadcrumbsProps, {}> {
  static defaultProps = {
    className: ""
  };

  render() {
    return (
      <ul className={`${Classes.BREADCRUMBS} ${this.props.className}`}>
        {this.props.children}
      </ul>
    );
  }
}

interface IBreadcrumbProps {
  className?: string;
  current?: boolean;
}

export class Breadcrumb extends React.Component<IBreadcrumbProps, {}> {
  static defaultProps = {
    className: "",
    current: false
  };

  render() {
    return (
      <li
        className={`${Classes.BREADCRUMB} ${
          this.props.current ? Classes.BREADCRUMB_CURRENT : ""
        } ${this.props.className}`}
      >
        {this.props.children}
      </li>
    );
  }
}
