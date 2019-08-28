import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { MetadataEntryFragment } from "./types/MetadataEntryFragment";
import { copyValue, assertUnreachable } from "../Util";
import { showCustomAlert } from "../CustomAlertProvider";
import { Button, Dialog, Classes, Colors, Icon } from "@blueprintjs/core";
import ReactMarkdown from "react-markdown";

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
                flex: 1,
                maxWidth: "max-content"
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
        ... on EventMarkdownMetadataEntry {
          mdString
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
            <Icon
              icon="clipboard"
              iconSize={10}
              color={"#a88860"}
              onClick={e => copyValue(e, entry.path)}
            />
          </>
        );

      case "EventJsonMetadataEntry":
        return (
          <MetadataEntryLink
            title="Show full value"
            onClick={() =>
              showCustomAlert({
                body: (
                  <div style={{ whiteSpace: "pre-wrap" }}>
                    {JSON.stringify(JSON.parse(entry.jsonString), null, 2)}
                  </div>
                ),
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
            <a href={entry.url} target="__blank">
              <Icon icon="link" iconSize={10} color={"#a88860"} />
            </a>
          </>
        );
      case "EventTextMetadataEntry":
        return entry.text;
      case "EventMarkdownMetadataEntry":
        return (
          <MarkdownMetadataLink title={entry.label} mdString={entry.mdString} />
        );
      default:
        return assertUnreachable(entry);
    }
  }
}

class MarkdownMetadataLink extends React.Component<{
  title: string;
  mdString: string;
}> {
  state = { isExpanded: false };
  onView = () => {
    this.setState({ isExpanded: true });
  };
  onClose = () => {
    this.setState({ isExpanded: false });
  };

  render() {
    const { mdString, title } = this.props;
    const { isExpanded } = this.state;
    return (
      <>
        <MetadataEntryLink onClick={this.onView}>
          [Show Metadata]
        </MetadataEntryLink>
        {isExpanded && (
          <Dialog
            icon="info-sign"
            usePortal={true}
            style={{ width: "auto", maxWidth: "80vw" }}
            title={title}
            onClose={this.onClose}
            isOpen={true}
          >
            <MarkdownMetadataExpanded>
              <ReactMarkdown source={mdString} />
            </MarkdownMetadataExpanded>

            <div className={Classes.DIALOG_FOOTER}>
              <div className={Classes.DIALOG_FOOTER_ACTIONS}>
                <Button
                  intent="primary"
                  autoFocus={true}
                  onClick={this.onClose}
                >
                  Close
                </Button>
              </div>
            </div>
          </Dialog>
        )}
      </>
    );
  }
}

const MarkdownMetadataExpanded = styled.div`
  font-size: 13px;
  overflow: auto;
  max-height: 500px;
  background: ${Colors.WHITE};
  border-top: 1px solid ${Colors.LIGHT_GRAY3};
  padding: 20px;
  margin: 0;
  margin-bottom: 20px;
`;

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
  width: 100%;
`;
