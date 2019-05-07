import * as React from "react";
import styled from "styled-components";
import { Toaster, Colors, Position, Intent } from "@blueprintjs/core";
import { IStepDisplayEvent } from "./RunMetadataProvider";

const SharedToaster = Toaster.create({ position: Position.TOP }, document.body);

interface DisplayEventProps {
  event: IStepDisplayEvent;
  showIcons?: boolean;
}

function isFilePath(url: string) {
  return url.startsWith("file://") || url.startsWith("/");
}

export class DisplayEvent extends React.Component<DisplayEventProps> {
  onCopyValue = async (event: React.MouseEvent<any>, value: string) => {
    event.preventDefault();

    const el = document.createElement("input");
    document.body.appendChild(el);
    el.value = value;
    el.select();
    document.execCommand("copy");
    el.remove();

    SharedToaster.show({
      message: "Copied to clipboard!",
      icon: "clipboard",
      intent: Intent.NONE
    });
  };

  render() {
    const { showIcons, event } = this.props;
    const value = event.value !== null ? event.value : "none";

    if (isFilePath(value)) {
      return (
        <DisplayEventContainer>
          {showIcons && FileIcon}
          {` ${event.key} `}
          <DisplayEventLink
            href={value}
            title={value}
            onClick={e => this.onCopyValue(e, value)}
          >
            [copy path]
          </DisplayEventLink>
        </DisplayEventContainer>
      );
    } else if (value.includes("://")) {
      return (
        <DisplayEventContainer>
          {showIcons && LinkIcon}
          {` ${event.key} `}
          <DisplayEventLink
            href={value}
            title={`Open ${value} in a new tab`}
            target="__blank"
          >
            [open link]
          </DisplayEventLink>
        </DisplayEventContainer>
      );
    }

    return (
      <DisplayEventContainer>
        {` ${event.key}: `}
        <DisplayEventLink
          href={value}
          title={`Copy ${value}`}
          onClick={e => this.onCopyValue(e, value)}
        >
          {value}
        </DisplayEventLink>
      </DisplayEventContainer>
    );
  }
}

const DisplayEventContainer = styled.div`
  padding: 2.5px 3px;
  white-space: pre-wrap;
  display: flex;
  font-size: 12px;
`;

const DisplayEventLink = styled.a`
  color: inherit;
  &:hover {
    color: inherit;
  }
`;

const FileIcon = (
  <svg width="20px" height="14px" viewBox="-100 0 350 242" version="1.1">
    <g stroke="none" strokeWidth="1" fill="none" fillRule="evenodd">
      <path
        d="M-100,96 L0,96"
        stroke="currentColor"
        strokeWidth="15"
        strokeLinecap="square"
      />
      <polygon
        stroke="currentColor"
        strokeWidth="15"
        points="5.4296875 236.507812 5.4296875 5.84765625 137.851562 5.84765625 188.003906 56 188.003906 236.507812"
      />
      <path
        d="M187.5,62.5078125 L130.5,62.5078125 M130.5,5.84765625 L130.5,62.5078125"
        stroke="currentColor"
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
