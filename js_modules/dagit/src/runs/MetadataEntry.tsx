import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { MetadataEntryFragment } from "./types/MetadataEntryFragment";
import { copyValue, assertUnreachable } from "../Util";
import { showCustomAlert } from "../CustomAlertProvider";
import { Icon } from "@blueprintjs/core";

export const MetadataEntries: React.FunctionComponent<{
  entries: MetadataEntryFragment[];
}> = props => (
  <span>
    <MetadataEntriesTable cellPadding="0" cellSpacing="0">
      <tbody>
        {props.entries.map((item, idx) => (
          <tr key={idx} style={{ display: "flex" }}>
            <td
              style={{
                flex: "0 0 auto",
                width: "max-content"
              }}
            >
              {item.label}
            </td>
            <td style={{ flex: 1 }}>
              <MetadataEntry entry={item} />
            </td>
          </tr>
        ))}
      </tbody>
    </MetadataEntriesTable>
  </span>
);

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
          <>
            <MetadataEntryLink
              title={"Copy to clipboard"}
              onClick={e => copyValue(e, entry.path)}
            >
              {entry.path}
            </MetadataEntryLink>{" "}
            <Icon icon="clipboard" iconSize={10} color={"#a88860"} />
          </>
        );

      case "EventJsonMetadataEntry":
        return (
          <MetadataEntryLink
            title="Show full value"
            onClick={() =>
              showCustomAlert({
                message: JSON.stringify(JSON.parse(entry.jsonString), null, 2),
                pre: true,
                title: "Value"
              })
            }
          >
            [Show Metadata]
          </MetadataEntryLink>
        );

      case "EventUrlMetadataEntry":
        return (
          <>
            <MetadataEntryLink
              href={entry.url}
              title={`Open in a new tab`}
              target="__blank"
            >
              {entry.url}
            </MetadataEntryLink>{" "}
            <Icon icon="link" iconSize={10} color={"#a88860"} />
          </>
        );
      case "EventTextMetadataEntry":
        return entry.text;
      default:
        return assertUnreachable(entry);
    }
  }
}

export const MetadataEntryLink = styled.a`
  text-decoration: underline;
  color: inherit;
  &:hover {
    color: inherit;
  }
`;

const MetadataEntriesTable = styled.table`
  padding: 0;
  margin-top: 4px;
  border-top: 1px solid #dbc5ad;
  border-left: 1px solid #dbc5ad;
  background: #fffaf5;
  td:first-child {
    color: #a88860;
  }
  td {
    padding: 4px;
    padding-right: 8px;
    border-bottom: 1px solid #dbc5ad;
    border-right: 1px solid #dbc5ad;
    vertical-align: top;
  }
`;
