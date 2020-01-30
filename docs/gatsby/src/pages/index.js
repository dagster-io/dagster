import React from "react";
import { Layout, SEO } from "systems/Core";
import { Redirect } from "@reach/router";
import version from "../../dagster-info";
const IndexPage = () => {
  return (
    <Layout>
      //{" "}
      <Redirect
        from="/"
        to={"/" + version.version + "/install/install"}
        noThrow
      />
      <SEO title="Home" />
    </Layout>
  );
};

export default IndexPage;
