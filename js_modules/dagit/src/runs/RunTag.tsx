import * as React from "react";
import { Tooltip, Tag, Position } from "@blueprintjs/core";
import styled from "styled-components/macro";
export const DAGSTER_TAG_NAMESPACE = "dagster/";

interface IRunTagProps {
  key: string;
  value: string;
}

export const RunTag = ({ tag }: { tag: IRunTagProps }) => {
  if (tag.key.startsWith(DAGSTER_TAG_NAMESPACE)) {
    const tagKey = tag.key.substr(DAGSTER_TAG_NAMESPACE.length);
    return (
      <Tooltip
        content={`${tag.key}=${tag.value}`}
        wrapperTagName="div"
        targetTagName="div"
        position={Position.LEFT}
      >
        <TagElement>
          <span
            style={{
              padding: "2px 5px",
              backgroundColor: "#7690BC"
            }}
          >
            {tagKey}
          </span>
          <span
            style={{
              padding: "2px 5px",
              backgroundColor: "#A5B9DA"
            }}
          >
            {tag.value}
          </span>
        </TagElement>
      </Tooltip>
    );
  }
  return (
    <TagElement>
      <span
        style={{
          padding: "2px 5px",
          // borderRight: "1px solid #999",
          backgroundColor: "#5C7080"
        }}
      >
        {tag.key}
      </span>
      <span style={{ padding: "2px 5px", backgroundColor: "#7d8c98" }}>
        {tag.value}
      </span>
    </TagElement>
  );
};

const TagElement = styled(Tag)`
  padding: 0 !important;
  margin: 1px !important;
  .bp3-fill {
    display: inline-flex;
  }
  overflow: hidden;
`;
