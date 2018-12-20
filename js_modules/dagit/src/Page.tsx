import * as React from "react";
import { Alignment, Navbar, NonIdealState } from "@blueprintjs/core";
import { History } from "history";
import navBarImage from "./images/nav-logo.png";

interface IPageProps {
  children: React.ReactNode;
  navbarContents?: React.ReactNode;
  history: History;
}

export default class Page extends React.Component<IPageProps> {
  handleHeadingClick = () => {
    this.props.history.push("/");
  };

  render() {
    return (
      <>
        <Navbar>
          <Navbar.Group align={Alignment.LEFT}>
            <Navbar.Heading onClick={this.handleHeadingClick}>
              <img src={navBarImage} style={{ height: 34 }} />
            </Navbar.Heading>
            <Navbar.Divider />
            {this.props.navbarContents}
          </Navbar.Group>
        </Navbar>
        {this.props.children}
      </>
    );
  }
}
