import { NextPage } from "next";

const Index: NextPage<{ userAgent: string }> = ({ userAgent }) => (
  <h1>This is the home page</h1>
);

export default Index;
