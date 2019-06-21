import * as React from "react";
import styled from "styled-components";
import { Toaster, Colors, Position, Intent } from "@blueprintjs/core";
import { IStepDisplayEvent } from "./RunMetadataProvider";
import { showCustomAlert } from "./CustomAlertProvider";

const SharedToaster = Toaster.create({ position: Position.TOP }, document.body);

interface DisplayEventProps {
  event: IStepDisplayEvent;
}

async function copyValue(event: React.MouseEvent<any>, value: string) {
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
}

const DisplayEventItem: React.FunctionComponent<
  IStepDisplayEvent["items"][0]
> = ({ action, actionText, actionValue, text }) => {
  let actionEl: React.ReactNode = actionText;

  if (action === "copy") {
    actionEl = (
      <DisplayEventLink
        title={"Copy to clipboard"}
        onClick={e => copyValue(e, actionValue)}
      >
        {actionText}
      </DisplayEventLink>
    );
  }
  if (action === "open-in-tab") {
    actionEl = (
      <DisplayEventLink
        href={actionValue}
        title={`Open in a new tab`}
        target="__blank"
      >
        {actionText}
      </DisplayEventLink>
    );
  }
  if (action === "show-in-modal") {
    actionEl = (
      <DisplayEventLink
        title="Show full value"
        onClick={() =>
          showCustomAlert({ message: actionValue, pre: true, title: "Value" })
        }
      >
        {actionText}
      </DisplayEventLink>
    );
  }
  return (
    <DisplayEventItemContainer>
      {text}: {actionEl}
    </DisplayEventItemContainer>
  );
};

export const DisplayEvent: React.FunctionComponent<DisplayEventProps> = ({
  event
}) => (
  <DisplayEventContainer>
    <DisplayEventHeader>
      {IconComponents[event.icon]}
      {event.text}
    </DisplayEventHeader>
    {event.items.map((item, idx) => (
      <DisplayEventItem {...item} key={idx} />
    ))}
  </DisplayEventContainer>
);

const DisplayEventContainer = styled.div`
  padding: 3.5px 3px;
  white-space: pre-wrap;
  font-size: 12px;
`;

const DisplayEventHeader = styled.div`
  display: flex;
  align-items: baseline;
  font-weight: 500;
`;

const DisplayEventItemContainer = styled.div`
  display: block;
  padding-left: 15px;
`;

const DisplayEventLink = styled.a`
  text-decoration: underline;
  color: inherit;
  &:hover {
    color: inherit;
  }
`;

const TinyStatusDot = styled.div`
  width: 10px;
  height: 7px;
  border-radius: 3px;
  margin-right: 4px;
  flex-shrink: 0;
`;

const IconComponents: { [key: string]: React.ReactNode } = {
  "dot-success": <TinyStatusDot style={{ background: Colors.GREEN2 }} />,
  "dot-failure": <TinyStatusDot style={{ background: Colors.RED2 }} />,
  "dot-pending": <TinyStatusDot style={{ background: Colors.GRAY2 }} />,
  none: <TinyStatusDot style={{ background: "transparent" }} />,
  file: (
    <img
      style={{ flexShrink: 0, alignSelf: "center" }}
      src={require("./images/icon-file.svg")}
    />
  ),
  link: (
    <img
      style={{ flexShrink: 0, alignSelf: "center" }}
      src={require("./images/icon-link.svg")}
    />
  )
};
