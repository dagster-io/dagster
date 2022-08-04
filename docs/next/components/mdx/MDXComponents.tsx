// This file contains components used by MDX files. It is important to be careful when changing these,
// because these components need to be backwards compatible. If you need to udpate a component with a
// breaking change, rename the existing component across the codebase and save a copy.

// For example, if you need to update `PyObject`, rename the existing component to `PyObjectLegacy`
// and update all existing usage of it

import React, { useContext, useRef, useState } from "react";

import Icons from "../Icons";
import Link from "../Link";
import { useVersion } from "../../util/useVersion";
import Image from "next/image";
import Zoom from "react-medium-image-zoom";
import "react-medium-image-zoom/dist/styles.css";
export const SearchIndexContext = React.createContext(null);
import path from "path";
import GenerateAgentToken from "./includes/dagster-cloud/GenerateAgentToken.mdx";
import BDCreateConfigureAgent from "./includes/dagster-cloud/BDCreateConfigureAgent.mdx";
import { Tab, Transition } from "@headlessui/react";

const PyObject: React.FunctionComponent<{
  module: string;
  object: string;
  method?: string;
  displayText?: string;
  pluralize?: boolean;
  decorator?: boolean;
}> = ({
  module = "dagster",
  object,
  method,
  displayText,
  pluralize = false,
  decorator = false,
}) => {
  const value = useContext(SearchIndexContext);
  if (!value) {
    return null;
  }

  const objects = value.objects as any;
  const moduleObjects = objects[module];
  const objectData = moduleObjects && moduleObjects[object];

  let textValue = displayText || object;
  if (pluralize) {
    textValue += "s";
  }
  if (decorator) {
    textValue = "@" + textValue;
  }
  if (method) {
    textValue += "." + method;
  }

  if (!moduleObjects || !objectData) {
    // TODO: broken link
    // https://github.com/dagster-io/dagster/issues/2939
    return (
      <a className="no-underline hover:underline" href="#">
        <code className="bg-red-100 p-1">{textValue}</code>
      </a>
    );
  }

  const fileIndex = objectData[0];
  // TODO: refer to all anchors available in apidocs
  // https://github.com/dagster-io/dagster/issues/3568
  const doc = value.docnames[fileIndex];
  const link = doc.replace("sections/api/apidocs/", "/_apidocs/");
  const methodSuffix = method ? "." + method : "";

  return (
    <Link href={link + "#" + module + "." + object + methodSuffix}>
      <a className="no-underline hover:underline">
        <code className="bg-blue-100 dark:bg-gray-700 p-1">{textValue}</code>
      </a>
    </Link>
  );
};

const Check = () => {
  return (
    <svg
      className="text-green-400 w-6 h-6 -mt-1 inline-block"
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
    >
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
        clipRule="evenodd"
      />
    </svg>
  );
};

const Cross = () => {
  return (
    <svg
      className="text-red-400 w-6 h-6 -mt-1 inline-block"
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
    >
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
        clipRule="evenodd"
      />
    </svg>
  );
};

const LinkGrid = ({ children }) => {
  return (
    <div className="rounded-lg bg-gray-200 dark:bg-gray-700 p-4 overflow-hidden shadow divide-y divide-gray-200 sm:divide-y-0 sm:grid sm:grid-cols-2 sm:gap-px">
      {children}
    </div>
  );
};

interface LinkGridItem {
  title: string;
  href: string;
  description: string;
}

function hashCode(str) {
  return str
    .split("")
    .reduce(
      (prevHash, currVal) =>
        ((prevHash << 5) - prevHash + currVal.charCodeAt(0)) | 0,
      0
    );
}

const getColorForString = (s: string) => {
  const colors = [
    ["bg-yellow-100 text-yellow-800"],
    ["bg-green-100 text-green-800"],
    ["bg-blue-100 text-blue-800"],
    ["bg-red-100 text-red-800"],
    ["bg-indigo-100 text-indigo-800"],
    ["bg-pink-100 text-pink-800"],
    ["bg-purple-100 text-purple-800"],
    ["bg-gray-100 text-gray-800"],
  ];

  return colors[Math.abs(hashCode(s)) % colors.length];
};

const Badge = ({ text }) => {
  const colors = getColorForString(text);
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-sm font-medium ${colors}`}
    >
      {text}
    </span>
  );
};

const LinkGridItem = ({ title, href, children, tags = [] }) => {
  return (
    <div className="rounded-tl-lg rounded-tr-lg sm:rounded-tr-none relative group bg-white dark:bg-gray-800 p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-indigo-500 hover:bg-gray-50 transition-colors">
      <div className="mt-8">
        <div className="text-lg font-medium">
          <Link href={href}>
            <a className="focus:outline-none">
              {/* Extend touch target to entire panel */}
              <span className="absolute inset-0" aria-hidden="true" />
              {title}
            </a>
          </Link>
        </div>
        <p className="mt-2 text-sm text-gray-500">{children}</p>
      </div>
      <span
        className="pointer-events-none absolute top-6 right-6 text-gray-300 group-hover:text-gray-400"
        aria-hidden="true"
      >
        <svg
          className="h-6 w-6"
          xmlns="http://www.w3.org/2000/svg"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path d="M20 4h1a1 1 0 00-1-1v1zm-1 12a1 1 0 102 0h-2zM8 3a1 1 0 000 2V3zM3.293 19.293a1 1 0 101.414 1.414l-1.414-1.414zM19 4v12h2V4h-2zm1-1H8v2h12V3zm-.707.293l-16 16 1.414 1.414 16-16-1.414-1.414z" />
        </svg>
      </span>
      <div className="space-x-2">
        {tags.map((tag) => (
          <Badge key={tag} text={tag} />
        ))}
      </div>
    </div>
  );
};

const ADMONITION_STYLES = {
  note: {
    colors: {
      bg: "primary-100",
      borderIcon: "primary-500",
      text: "primary-500",
    },
    icon: Icons.InfoCircle,
  },
  warning: {
    colors: { bg: "yellow-50", borderIcon: "yellow-400", text: "yellow-700" },
    icon: Icons.Warning,
  },
};

const Admonition = ({ style, children }) => {
  const { colors, icon } = ADMONITION_STYLES[style];
  return (
    <div
      className={`bg-${colors.bg} border-l-4 border-${colors.borderIcon} px-4 my-4`}
    >
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <svg
            className={`h-5 w-5 text-${colors.borderIcon}`}
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 25 25"
            fill="currentColor"
            aria-hidden="true"
          >
            {icon}
          </svg>
        </div>
        <div className="ml-3">
          <p className={`text-sm text-${colors.text}`}>{children}</p>
        </div>
      </div>
    </div>
  );
};

const Note = ({ children }) => {
  return <Admonition style="note">{children}</Admonition>;
};

const Warning = ({ children }) => {
  return <Admonition style="warning">{children}</Admonition>;
};

const CodeReferenceLink = ({ filePath, isInline, children }) => {
  const { version } = useVersion();
  const url = `https://github.com/dagster-io/dagster/tree/${version}/${filePath}`;

  if (isInline) {
    return <a href={url}>{children}</a>;
  } else {
    return (
      <div className="bg-primary-100 rounded flex item-center p-4">
        <div>
          <svg
            className="h-8 w-8 text-primary-900"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M8.128 19.825a1.586 1.586 0 0 1-1.643-.117 1.543 1.543 0 0 1-.53-.662 1.515 1.515 0 0 1-.096-.837l.736-4.247-3.13-3a1.514 1.514 0 0 1-.39-1.569c.09-.271.254-.513.475-.698.22-.185.49-.306.776-.35L8.66 7.73l1.925-3.862c.128-.26.328-.48.577-.633a1.584 1.584 0 0 1 1.662 0c.25.153.45.373.577.633l1.925 3.847 4.334.615c.29.042.562.162.785.348.224.186.39.43.48.704a1.514 1.514 0 0 1-.404 1.58l-3.13 3 .736 4.247c.047.282.014.572-.096.837-.111.265-.294.494-.53.662a1.582 1.582 0 0 1-1.643.117l-3.865-2-3.865 2z" />
          </svg>
        </div>
        <div className="pl-4 pt-1">
          You can find the code for this example on <a href={url}>Github</a>
        </div>
      </div>
    );
  }
};

const ReferenceTable = ({ children }) => {
  return (
    <table
      className="table"
      style={{
        width: "100%",
      }}
    >
      <thead>
        <tr>
          <th>Property</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>
        {children}
      </tbody>
    </table>
  );
};

const ReferenceTableItem = ({ propertyName, children }) => {
  return (
    <tr>
      <td
        style={{
        width: "40%",
        }}
        >
        {propertyName}
      </td>
      <td>
        {children}
      </td>
    </tr>
  );
};

const InstanceDiagramBox = ({ href = "#", className = "", children }) => {
  return (
    <a
      href={href}
      className={`bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 flex-1 h-16 rounded flex justify-center items-center font-medium ${className}`}
    >
      {children}
    </a>
  );
};

const TODO = () => {
  return (
    <div className="h-48 w-full bg-red-100 flex justify-center items-center rounded-lg">
      <span className="font-bold">TODO</span>
    </div>
  );
};

const PlaceholderImage = ({ caption = "Placeholder Image" }) => {
  return (
    <div className="h-48 w-full bg-gray-100 flex justify-center items-center rounded-lg">
      <span className="font-bold">{caption}</span>
    </div>
  );
};

const Experimental = () => {
  return (
    <div className="inline-flex items-center px-3 py-0.5 rounded-full align-baseline text-xs uppercase font-medium bg-sea-foam text-gable-green">
      Experimental
    </div>
  );
};

const Pre = ({ children, ...props }) => {
  const preRef = useRef<HTMLPreElement>(null);
  const [copied, setCopied] = useState(false);

  const onClick = async () => {
    try {
      await navigator.clipboard.writeText(preRef.current?.innerText);
      setCopied(true);
    } catch (err) {
      console.log("Fail to copy", err);
    }

    setTimeout(() => {
      setCopied(false);
    }, 1000);
  };

  return (
    <div className="relative">
      <Transition
        show={!copied}
        appear={true}
        enter="transition ease-out duration-150 transform"
        enterFrom="opacity-0 scale-95"
        enterTo="opacity-100 scale-100"
        leave="transition ease-in duration-150 transform"
        leaveFrom="opacity-100 scale-100"
        leaveTo="opacity-0 scale-95"
      >
        <div className="absolute top-0 right-0 mt-2 mr-2">
          <svg
            className="h-5 w-5 text-gray-400 cursor-pointer hover:text-gray-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            onClick={onClick}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
        </div>
      </Transition>
      <Transition
        show={copied}
        appear={true}
        enter="transition ease-out duration-150 transform"
        enterFrom="opacity-0 scale-95"
        enterTo="opacity-500 scale-100"
        leave="transition ease-in duration-200 transform"
        leaveFrom="opacity-100 scale-100"
        leaveTo="opacity-0 scale-95"
      >
        <div className="absolute top-0 right-0 mt-1 mr-2">
          <span className="inline-flex items-center px-2 rounded text-xs font-medium leading-4 bg-gray-100 text-gray-800">
            Copied
          </span>
        </div>
      </Transition>
      <pre ref={preRef} {...(props as any)}>
        {children}
      </pre>
    </div>
  );
};

const ArticleList = ({ children }) => {
  return (
    <div className="category-container">
      <div className="category-inner-container">
        <ul
          style={{
            columnCount: 2,
            columnGap: "20px",
            padding: 0,
            margin: 0,
          }}
        >
          {children}
        </ul>
      </div>
    </div>
  );
};

const ArticleListItem = ({ title, href }) => {
  return (
    <li
      style={{
        marginTop: 0,
      }}
    >
      <Link href={href}>{title}</Link>
    </li>
  );
};

interface Entry {
  name: string;
  content: any;
}

function classNames(...classes) {
  return classes.filter(Boolean).join(" ");
}

function TabGroup({ entries }: { entries: Entry[] }) {
  return (
    <div className="w-full px-2 py-2 sm:px-0">
      <Tab.Group>
        <Tab.List className="flex space-x-2 m-2">
          {entries.map((entry, idx) => (
            <Tab
              key={idx}
              className={({ selected }) =>
                classNames(
                  "w-full py-3 text-sm font-bold leading-5",
                  "focus:outline-none border-gray-200",
                  selected
                    ? "border-b-2 border-primary-500 text-primary-500"
                    : "border-b hover:border-gray-500 hover:text-gray-700"
                )
              }
            >
              {entry?.name}
            </Tab>
          ))}
        </Tab.List>
        <Tab.Panels>
          {entries.map((entry, idx) => (
            <Tab.Panel key={idx} className={classNames("p-3")}>
              {entry?.content}
            </Tab.Panel>
          ))}
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
}

export default {
  a: ({ children, ...props }) => {
    // Skip in-page links and external links
    if (!props.href.startsWith("/")) {
      return <a {...props}>{children}</a>;
    }
    // Hydrate the links in raw MDX to include versions
    return (
      <Link href={props.href}>
        <a {...props}> {children}</a>
      </Link>
    );
  },
  img: ({ children, ...props }) => (
    <span className="block mx-auto">
      <img {...(props as any)} />
    </span>
  ),
  Image: ({ children, ...props }) => {
    /* Only version images when all conditions meet:
     * - use <Image> component in mdx
     * - on non-master version
     * - in public/images/ dir
     */
    const { version } = useVersion();
    const { src } = props;
    if (!src.startsWith("/images/")) {
      return (
        <span className="block mx-auto">
          <Image {...(props as any)} />
        </span>
      );
    }

    const resolvedPath =
      version === "master"
        ? src
        : new URL(
            path.join("versioned_images", version, src.replace("/images/", "")),
            "https://dagster-docs-versioned-content.s3.us-west-1.amazonaws.com"
          ).href;

    return (
      <Zoom wrapElement="span" wrapStyle={{ display: "block" }}>
        <span className="block mx-auto">
          <Image
            src={resolvedPath}
            width={props.width}
            height={props.height}
            alt={props.alt}
          />
        </span>
      </Zoom>
    );
  },
  pre: Pre,
  PyObject,
  Link,
  Check,
  Cross,
  LinkGrid,
  LinkGridItem,
  Note,
  Warning,
  CodeReferenceLink,
  InstanceDiagramBox,
  TODO,
  PlaceholderImage,
  Experimental,
  Icons,
  ReferenceTable,
  ReferenceTableItem,
  GenerateAgentToken,
  BDCreateConfigureAgent,
  ArticleList,
  ArticleListItem,
  TabGroup,
};
