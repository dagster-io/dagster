import * as React from "react";
import { Alignment, Navbar } from "@blueprintjs/core";

export default class Page extends React.Component {
  public render() {
    return (
      <>
        <Navbar>
          <Navbar.Group align={Alignment.LEFT}>
            <Navbar.Heading>
              <img src={require('./images/nav-logo.png')} style={{ height: 34 }} />
            </Navbar.Heading>
            <Navbar.Divider />
          </Navbar.Group>
        </Navbar>
        {this.props.children}
      </>
    );
  }
}
