// Import the original mapper
import CliInvocationExample from '../components/CliInvocationExample';
import {Changelog} from '../components/Changelog';
import CodeExample from '../components/CodeExample';
import Link from '@docusaurus/Link';
import MDXComponents from '@theme-original/MDXComponents';
import TOCInline from '@theme/TOCInline';
import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';
import WideContent from '../components/WideContent';
import {CodeReferenceLink} from '../components/CodeReferenceLink';
import {PackageInstallInstructions} from '../components/PackageInstall';
import {PyObject} from '../components/PyObject';
export default {
  // Re-use the default mapping
  ...MDXComponents,
  CliInvocationExample,
  Changelog,
  CodeExample,
  CodeReferenceLink,
  Link,
  PackageInstallInstructions,
  PyObject,
  TOCInline,
  TabItem,
  Tabs,
  WideContent,
};
