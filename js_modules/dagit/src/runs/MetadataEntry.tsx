import * as React from "react";
import styled from "styled-components";
import { MetadataEntryFragment } from "./types/MetadataEntryFragment";
import { copyValue, assertUnreachable } from "../Util";
import { showCustomAlert } from "../CustomAlertProvider";
import gql from "graphql-tag";
import { Colors } from "@blueprintjs/core";

export const MetadataEntries: React.FunctionComponent<{
  entries: MetadataEntryFragment[];
}> = props => (
  <span style={{ flex: 1 }}>
    <MetadataEntriesTable cellPadding="0" cellSpacing="0">
      <thead>
        <tr>
          <td style={{ minWidth: 100 }}>Label</td>
          <td>Value</td>
        </tr>
      </thead>
      <tbody>
        {props.entries.map((item, idx) => (
          <tr key={idx}>
            <td>{item.label}</td>
            <td>
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
          <MetadataEntryLink
            title={"Copy to clipboard"}
            onClick={e => copyValue(e, entry.path)}
          >
            [Copy Path]
          </MetadataEntryLink>
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
          <MetadataEntryLink
            href={entry.url}
            title={`Open in a new tab`}
            target="__blank"
          >
            [Open URL]
          </MetadataEntryLink>
        );
      case "EventTextMetadataEntry":
        return entry.text;
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

const MetadataEntriesTable = styled.table`
  padding: 0;
  min-width: 50%;
  thead td {
    padding-left: 4px;
    padding-right: 8px;
    color: ${Colors.GRAY3};
    text-transform: uppercase;
    font-size: 11px;
    border-bottom: 1px solid ${Colors.LIGHT_GRAY1};
  }
  tbody td {
    padding: 4px;
    padding-right: 8px;
    border-bottom: 1px solid ${Colors.LIGHT_GRAY3};
    border-right: 1px solid ${Colors.LIGHT_GRAY3};
    &:last-child {
      border-right: 0;
    }
  }
  tbody tr:last-child {
    td {
      border-bottom: 0;
    }
  }
`;
