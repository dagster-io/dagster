import React from "react";
import { Layout, SEO } from "systems/Core";
import { Redirect } from "@reach/router";

import { useVersion } from "systems/Version";

const IndexPage = () => {
  const { version } = useVersion();
  return (
    <Layout>
      <Redirect from="/" to={`/${version.current}/install/`} noThrow />
      <SEO title="Home" />
    </Layout>
  );
};

export default IndexPage;
