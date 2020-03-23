import { NextPage } from "next";

const APIIndex: NextPage<{ userAgent: string }> = ({ userAgent }) => (
  <h1>API Index</h1>
);

export default APIIndex;
