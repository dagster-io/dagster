import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { Query, QueryResult } from "react-apollo";
import { GetTypeDetailsQuery } from "./types/GetTypeDetailsQuery";
import Loading from "../Loading";

const GET_TYPE_DETAILS = gql`
  query GetTypeDetailsQuery($pipelineName: String!, $typeName: String!) {
    type(pipelineName: $pipelineName, typeName: $typeName) {
      name
      description
      typeAttributes {
        isBuiltin
        isSystemConfig
      }
    }
  }
`;

interface IPipelineTypeOverlayProps {
  root: { x: number; y: number };
  pipelineName: string;
  typeName: string;
}

export default class PipelineTypeOverlay extends React.Component<
  IPipelineTypeOverlayProps & React.HTMLProps<HTMLDivElement>
> {
  render() {
    const { root, ref, pipelineName, typeName, ...rest } = this.props;

    return (
      <OverlayContainer
        {...rest}
        style={{ left: `${root.x}px`, top: `${root.y}px` }}
        onWheel={e => e.stopPropagation()}
        onScroll={e => e.stopPropagation()}
      >
        <OverlayContent>
          <Query
            query={GET_TYPE_DETAILS}
            variables={{ pipelineName: pipelineName, typeName: typeName }}
          >
            {(queryResult: QueryResult<GetTypeDetailsQuery, any>) => (
              <Loading queryResult={queryResult}>
                {data => (
                  <TypeDescription>
                    {data.type &&
                      (
                        data.type.description || "No description provided."
                      ).trim()}
                  </TypeDescription>
                )}
              </Loading>
            )}
          </Query>
        </OverlayContent>
        <OverlayTriangle />
      </OverlayContainer>
    );
  }
}

const OverlayContainer = styled.div`
  position: absolute;
  transform: translate3d(-50%, -100%, 0);
`;

const OverlayContent = styled.div`
  padding: 0.5em;
  background: ${Colors.WHITE};
  border-radius: 2px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
  min-width: 240px;
  max-width: 400px;
  max-height: 180px;
  overflow-y: scroll;
`;

const OverlayTriangle = styled.div`
  width: 12px;
  height: 24px;
  margin: auto;
  position: relative;
  z-index: 2;
  border-top: solid 12px ${Colors.WHITE};
  border-left: solid 12px transparent;
  border-right: solid 12px transparent;
`;

const TypeDescription = styled.div`
  white-space: pre-line;
`;
