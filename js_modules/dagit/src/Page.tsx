import * as React from "react";
import { Alignment, Navbar } from "@blueprintjs/core";
import { History } from "history";
import navBarImage from "./images/nav-logo.png";
import WebsocketStatus from "./WebsocketStatus";
import VersionLabel from "./VersionLabel";

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
          <Navbar.Group align={Alignment.RIGHT}>
            <WebsocketStatus />
            <VersionLabel />
          </Navbar.Group>
        </Navbar>
        {this.props.children}
      </>
    );
  }
}
