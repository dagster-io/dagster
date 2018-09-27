import * as React from "react";
import { Alignment, Navbar } from "@blueprintjs/core";
import navBarImage from "./images/nav-logo.png";

export default class Page extends React.Component {
  public render() {
    return (
      <>
        <Navbar style={{ zIndex: 1 }}>
          <Navbar.Group align={Alignment.LEFT}>
            <Navbar.Heading>
              <img src={navBarImage} style={{ height: 34 }} />
            </Navbar.Heading>
            <Navbar.Divider />
          </Navbar.Group>
        </Navbar>
        {this.props.children}
      </>
    );
  }
}
