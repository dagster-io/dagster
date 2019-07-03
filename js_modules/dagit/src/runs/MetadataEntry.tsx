import * as React from "react";
import styled from "styled-components";
import { MetadataEntryFragment } from "./types/MetadataEntryFragment";
import { copyValue, assertUnreachable } from "../Util";
import { showCustomAlert } from "../CustomAlertProvider";
import gql from "graphql-tag";

export class MetadataEntry extends React.Component<{
  entry: MetadataEntryFragment;
}> {
  static fragments = {
    MetadataEntryFragment: gql`
      fragment MetadataEntryFragment on EventMetadataEntry {
        __typename
        label
        description
        ... on EventPathMetadataEntry {
          path
        }
        ... on EventJsonMetadataEntry {
          jsonString
        }
        ... on EventUrlMetadataEntry {
          url
        }
        ... on EventTextMetadataEntry {
          text
        }
      }
    `
  };
  render() {
    const { entry } = this.props;
    switch (entry.__typename) {
      case "EventPathMetadataEntry":
        return (
          <div>
            {`${entry.label}: `}
            <MetadataEntryLink
              title={"Copy to clipboard"}
              onClick={e => copyValue(e, entry.path)}
            >
              [Copy Path]
            </MetadataEntryLink>
          </div>
        );

      case "EventJsonMetadataEntry":
        return (
          <div>
            {`${entry.label}: `}
            <MetadataEntryLink
              title="Show full value"
              onClick={() =>
                showCustomAlert({
                  message: JSON.stringify(
                    JSON.parse(entry.jsonString),
                    null,
                    2
                  ),
                  pre: true,
                  title: "Value"
                })
              }
            >
              [Show Metadata]
            </MetadataEntryLink>
          </div>
        );

      case "EventUrlMetadataEntry":
        return (
          <div>
            {`${entry.label}: `}
            <MetadataEntryLink
              href={entry.url}
              title={`Open in a new tab`}
              target="__blank"
            >
              [Open URL]
            </MetadataEntryLink>
          </div>
        );
      case "EventTextMetadataEntry":
        return <div>{`${entry.label}: ${entry.text}`}</div>;
      default:
        return assertUnreachable(entry);
    }
  }
}

const MetadataEntryLink = styled.a`
  text-decoration: underline;
  color: inherit;
  &:hover {
    color: inherit;
  }
`;
