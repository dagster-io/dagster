import * as React from "react";
import styled from "styled-components";
import { Toaster, Colors, Position, Intent } from "@blueprintjs/core";

const SharedToaster = Toaster.create({ position: Position.TOP }, document.body);

interface MaterializationProps {
  fileLocation: string;
  fileName: string;
}

function isFilePath(url: string) {
  return url.startsWith("file://") || url.startsWith("/");
}
export class Materialization extends React.Component<MaterializationProps> {
  onCopyPath = async (path: string) => {
    const el = document.createElement("input");
    document.body.appendChild(el);
    el.value = path;
    el.select();
    document.execCommand("copy");
    el.remove();

    SharedToaster.show({
      message: "File path copied to clipboard",
      icon: "clipboard",
      intent: Intent.NONE
    });
  };

  render() {
    const { fileLocation, fileName } = this.props;

    if (isFilePath(fileLocation)) {
      return (
        <MaterializationLink
          href={fileLocation}
          key={fileLocation}
          title={`Copy path to ${fileLocation}`}
          onClick={e => {
            e.preventDefault();
            this.onCopyPath(fileLocation);
          }}
        >
          {FileIcon} {fileName}
        </MaterializationLink>
      );
    }
    return (
      <MaterializationLink
        href={fileLocation}
        key={fileLocation}
        title={`Open ${fileLocation} in a new tab`}
        target="__blank"
      >
        {LinkIcon} {fileName}
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

const LinkIcon = (
  <svg width="20px" height="14px" viewBox="-300 -100 1200 1200" version="1.1">
    <g>
      <path
        fill={Colors.GRAY5}
        d="M568.2,644.1c-54.4,0-108.7-20.7-150.1-62.1c-11.2-11.2-11.2-29.5,0-40.8c11.2-11.2,29.5-11.2,40.8,0c60.3,60.3,158.4,60.3,218.7,0l209.6-209.6c60.3-60.3,60.3-158.4,0-218.7c-60.3-60.3-158.4-60.3-218.7,0L491.6,289.7c-11.2,11.2-29.5,11.2-40.8,0c-11.2-11.2-11.2-29.5,0-40.8L627.7,72.1c82.8-82.8,217.5-82.8,300.2,0c82.7,82.8,82.8,217.5,0,300.2L718.3,582C676.9,623.4,622.5,644.1,568.2,644.1L568.2,644.1L568.2,644.1z M222.2,990c-54.4,0-108.7-20.7-150.1-62.1c-82.8-82.8-82.8-217.5,0-300.2L281.7,418c82.8-82.8,217.5-82.8,300.2,0c11.2,11.2,11.2,29.5,0,40.8c-11.2,11.2-29.5,11.2-40.8,0c-60.3-60.3-158.4-60.3-218.7,0L112.9,668.4c-60.3,60.3-60.3,158.4,0,218.7c60.3,60.3,158.4,60.3,218.7,0l176.9-176.9c11.2-11.2,29.5-11.2,40.8,0c11.2,11.2,11.2,29.5,0,40.8L372.3,927.9C330.9,969.3,276.6,990,222.2,990L222.2,990L222.2,990z"
      />
    </g>
  </svg>
);
