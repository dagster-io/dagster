// Import the original mapper
import MDXComponents from "@theme-original/MDXComponents";
import { PyObject } from "../components/PyObject";
import CodeExample from "../components/CodeExample";
import Tabs from "@theme/Tabs";
import TabItem from "@theme/TabItem";
export default {
  // Re-use the default mapping
  ...MDXComponents,
  PyObject,
  Tabs,
  TabItem,
  CodeExample,
};
