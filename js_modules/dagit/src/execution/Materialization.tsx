import * as React from "react";
import styled from "styled-components";
import { ROOT_SERVER_URI } from "../Util";
import { Colors, Spinner } from "@blueprintjs/core";

function fileLocationToHref(location: string) {
  if (location.startsWith("/")) {
    return `file://${location}`;
  }
  return location;
}

interface MaterializationProps {
  fileLocation: string;
  fileName: string;
}
interface MaterializationState {
  opening: boolean;
}

export class Materialization extends React.Component<
  MaterializationProps,
  MaterializationState
> {
  state = {
    opening: false
  };

  _openingTimeout?: NodeJS.Timeout;

  componentWillUnmount() {
    if (this._openingTimeout) {
      clearTimeout(this._openingTimeout);
    }
  }

  onOpenFileLink = async (event: React.MouseEvent<HTMLAnchorElement>) => {
    const url = event.currentTarget.href;

    // If the file's location is a path, tell dagit to open it on the machine.
    if (url.startsWith("file://")) {
      event.preventDefault();

      // Display a loading spinner to give Dagit and the file handler (eg: jupyter notebooks)
      // time to open the file. Otherwise the user might just think its not working. Just
      // set to an arbitrary amount of time - jupyter is slow.
      this.setState({ opening: true });
      this._openingTimeout = setTimeout(() => {
        this.setState({ opening: false });
      }, 2000);

      const path = url.replace("file://", "");
      const result = await fetch(
        `${ROOT_SERVER_URI}/dagit/open?path=${encodeURIComponent(path)}`
      );

      if (result.status !== 200) {
        const error = await result.text();
        this.setState({ opening: false });
        alert(`Dagit was unable to open the file.\n\n${error}`);
      }
    } else {
      // If the file's location is a URL, allow the browser to open it normally.
    }
  };

  render() {
    const { fileLocation, fileName } = this.props;

    return (
      <MaterializationLink
        onClick={this.onOpenFileLink}
        href={fileLocationToHref(fileLocation)}
        key={fileLocation}
        title={fileLocation}
        target="__blank"
      >
        {this.state.opening ? (
          <span style={{ paddingLeft: 3, paddingRight: 3 }}>
            <Spinner size={14} />
          </span>
        ) : (
          FileIcon
        )}{" "}
        {fileName}
      </MaterializationLink>
    );
  }
}

const MaterializationLink = styled.a`
  display: block;
  color: ${Colors.GRAY3};
  display: inline-block;
  padding: 6px 3px;
  padding-left: 23px;
  display: inline-flex;
  font-size: 12px;
  &:hover {
    color: ${Colors.WHITE};
  }
`;

const FileIcon = (
  <svg width="20px" height="14px" viewBox="-100 0 350 242" version="1.1">
    <g stroke="none" strokeWidth="1" fill="none" fillRule="evenodd">
      <path
        d="M-100,96 L0,96"
        stroke={Colors.GRAY3}
        strokeWidth="15"
        strokeLinecap="square"
      />
      <polygon
        stroke={Colors.GRAY3}
        strokeWidth="15"
        points="5.4296875 236.507812 5.4296875 5.84765625 137.851562 5.84765625 188.003906 56 188.003906 236.507812"
      />
      <path
        d="M187.5,62.5078125 L130.5,62.5078125 M130.5,5.84765625 L130.5,62.5078125"
        stroke={Colors.GRAY3}
        strokeWidth="15"
        strokeLinecap="square"
      />
    </g>
  </svg>
);
