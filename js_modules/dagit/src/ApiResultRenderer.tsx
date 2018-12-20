import * as React from "react";
import gql from "graphql-tag";
import { Query, QueryResult } from "react-apollo";
import Loading from "./Loading";
import MOCKS from "./__tests__/mockData";

export default class ApiResultRenderer extends React.Component {
  render() {
    return MOCKS.reduce((children, mock) => {
      return (
        <Query query={mock.request.query} variables={mock.request.variables}>
          {(queryResult: QueryResult<any, any>) => (
            <>
              <Loading queryResult={queryResult}>
                {data => (
                  <pre>
                    {`
{
  request: {
    operationName: "${mock.request.operationName}",
    queryVariableName: "${mock.request.queryVariableName}",
    query: ${mock.request.queryVariableName},
    variables: ${JSON.stringify(mock.request.variables)}
  },
  result: {
    data: ${JSON.stringify(data)}
  },
},`}
                  </pre>
                )}
              </Loading>
              {children}
            </>
          )}
        </Query>
      );
    }, <div />);
  }
}
