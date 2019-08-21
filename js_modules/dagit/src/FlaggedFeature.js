import { Query } from "react-apollo";
import React from "react";
import gql from "graphql-tag";

class FlaggedFeature extends React.Component {
  render() {
    const { children, name } = this.props;

    return (
      <Query query={ENABLED_FEATURES_ROOT_QUERY} fetchPolicy="cache-first">
        {({ data }) => {
          if (!data || !data.enabledFeatures) return null;
          const hasFeature = data.enabledFeatures.some(
            feature => feature.toLowerCase() === name.toLowerCase()
          );

          return hasFeature ? children : null;
        }}
      </Query>
    );
  }
}

export const ENABLED_FEATURES_ROOT_QUERY = gql`
  query EnabledFeaturesRootQuery {
    enabledFeatures
  }
`;

export default FlaggedFeature;
