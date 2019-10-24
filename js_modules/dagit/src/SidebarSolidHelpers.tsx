import * as React from "react";
import styled from "styled-components";
import { Link } from "react-router-dom";
import { Text, Code, Colors } from "@blueprintjs/core";

import { titleOfIO } from "./Util";
import { SectionHeader } from "./SidebarComponents";
import { SolidColumn } from "./runs/LogsRowComponents";

export type SolidLinkInfo = {
  solid: { name: string };
  definition: { name: string };
};

export interface SidebarSolidInvocationInfo {
  handleID: string;
  pipelineName?: string;
}

export type SolidMappingTable = {
  [key: string]: SolidLinkInfo[];
};

export const ShowAllButton = styled.button`
  background: transparent;
  border: none;
  color: ${Colors.BLUE3};
  text-decoration: underline;
  padding-top: 10px;
  font-size: 0.9rem;
`;

export const TypeWrapper = styled.div`
  margin-bottom: 10px;
`;

export const SolidLink = (props: SolidLinkInfo) => (
  <Link to={`./${props.solid.name}`}>
    <Code
      style={{
        display: "inline-block",
        verticalAlign: "middle",
        textOverflow: "ellipsis",
        overflow: "hidden",
        maxWidth: "100%"
      }}
    >
      {titleOfIO(props)}
    </Code>
  </Link>
);

export const SolidLinks = (props: { title: string; items: SolidLinkInfo[] }) =>
  props.items && props.items.length ? (
    <Text>
      {props.title}
      {props.items.map((i, idx) => (
        <SolidLink key={idx} {...i} />
      ))}
    </Text>
  ) : null;

export const Invocation = (props: {
  invocation: SidebarSolidInvocationInfo;
  onClick: () => void;
}) => {
  const { handleID, pipelineName } = props.invocation;
  const handlePath = handleID.split(".");
  return (
    <InvocationContainer onClick={props.onClick}>
      {pipelineName && (
        <div style={{ color: Colors.BLUE1 }}>{pipelineName}</div>
      )}
      <SolidColumn stepKey={handlePath.join(".")} />
    </InvocationContainer>
  );
};

export const DependencyRow = ({
  from,
  to
}: {
  from: SolidLinkInfo | string;
  to: SolidLinkInfo | string;
}) => {
  return (
    <tr>
      <td
        style={{
          whiteSpace: "nowrap",
          maxWidth: 0,
          width: "45%"
        }}
      >
        {typeof from === "string" ? (
          <DependencyLocalIOName>{from}</DependencyLocalIOName>
        ) : (
          <SolidLink {...from} />
        )}
      </td>
      <td>{DependencyArrow}</td>
      <td
        style={{
          textOverflow: "ellipsis",
          overflow: "hidden",
          whiteSpace: "nowrap",
          maxWidth: 0,
          width: "60%"
        }}
      >
        {typeof to === "string" ? (
          <DependencyLocalIOName>{to}</DependencyLocalIOName>
        ) : (
          <SolidLink {...to} />
        )}
      </td>
    </tr>
  );
};

export const ResourceHeader = styled(SectionHeader)`
  font-size: 13px;
`;

export const ResourceContainer = styled.div`
  display: flex;
  align-items: flex-start;
  padding-top: 15px;
  & .bp3-icon {
    padding-top: 7px;
    padding-right: 10px;
  }
  &:first-child {
    padding-top: 0;
  }
`;

export const DependencyLocalIOName = styled.div`
  font-family: monospace;
  font-size: smaller;
  font-weight: 500;
  color: ${Colors.BLACK};
`;

export const DependencyTable = styled.table`
  width: 100%;
`;

export const InvocationContainer = styled.div`
  margin: 0 -10px;
  padding: 10px;
  pointer: default;
  border-bottom: 1px solid ${Colors.LIGHT_GRAY2};
  &:last-child {
    border-bottom: none;
  }
  &:hover {
    background: ${Colors.LIGHT_GRAY5};
  }
  font-family: monospace;
`;

export const DependencyArrow = (
  <svg width="36px" height="9px" viewBox="0 0 36 9" version="1.1">
    <g opacity="0.682756696">
      <g
        transform="translate(-1127.000000, -300.000000)"
        fill="#979797"
        fillRule="nonzero"
      >
        <g transform="translate(120.000000, 200.000000)">
          <path d="M1033.16987,105 L1007.67526,105 L1007.67526,104 L1033.16987,104 L1033.16987,100 L1042.16987,104.5 L1033.16987,109 L1033.16987,105 Z" />
        </g>
      </g>
    </g>
  </svg>
);
