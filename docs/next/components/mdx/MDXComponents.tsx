// This file contains components used by MDX files. It is important to be careful when changing these,
// because these components need to be backwards compatible. If you need to udpate a component with a
// breaking change, rename the existing component across the codebase and save a copy.

// For example, if you need to update `PyObject`, rename the existing component to `PyObjectLegacy`
// and update all existing usage of it
import {LATEST_VERSION} from 'util/version';

import {Tab, Transition} from '@headlessui/react';
import cx from 'classnames';
import {PersistentTabContext} from 'components/PersistentTabContext';
import NextImage from 'next/image';
import NextLink from 'next/link';
import React, {ReactElement, useCallback, useContext, useEffect, useRef, useState} from 'react';
import Zoom from 'react-medium-image-zoom';

import Icons from '../Icons';
import Link from '../Link';
//  import {Note, Warning} from '../markdoc/Callouts';

import 'react-medium-image-zoom/dist/styles.css';
import {RenderedDAG} from './RenderedDAG';
import EnvVarsBenefits from './includes/EnvVarsBenefits.mdx';
import EnvironmentVariablesIntro from './includes/EnvironmentVariablesIntro.mdx';
import ExperimentalCallout from './includes/ExperimentalCallout.mdx';
import AddGitlabVariable from './includes/dagster-cloud/AddGitlabVariable.mdx';
import AddGitubRepositorySecret from './includes/dagster-cloud/AddGitubRepositorySecret.mdx';
import ApplicableCloudPlan from './includes/dagster-cloud/ApplicableCloudPlan.mdx';
import ApplicableDagsterProduct from './includes/dagster-cloud/ApplicableDagsterProduct.mdx';
import AssetCheckAlerts from './includes/dagster-cloud/AssetCheckAlerts.mdx';
import BDCreateConfigureAgent from './includes/dagster-cloud/BDCreateConfigureAgent.mdx';
import GenerateAgentToken from './includes/dagster-cloud/GenerateAgentToken.mdx';
import ScimSupportedFeatures from './includes/dagster-cloud/ScimSupportedFeatures.mdx';
import AmazonEcsEnvVarsConfiguration from './includes/dagster-cloud/agents/AmazonEcsEnvVarsConfiguration.mdx';
import DockerEnvVarsConfiguration from './includes/dagster-cloud/agents/DockerEnvVarsConfiguration.mdx';
import K8sEnvVarsConfiguration from './includes/dagster-cloud/agents/K8sEnvVarsConfiguration.mdx';
import DagsterDevTabs from './includes/dagster/DagsterDevTabs.mdx';
import DagsterVersion from './includes/dagster/DagsterVersion.mdx';
import RawComputeLogs from './includes/dagster/concepts/logging/RawComputeLogs.mdx';
import StructuredEventLogs from './includes/dagster/concepts/logging/StructuredEventLogs.mdx';
import DbtModelAssetExplanation from './includes/dagster/integrations/DbtModelAssetExplanation.mdx';

export const SearchIndexContext = React.createContext(null);

// https://www.30secondsofcode.org/react/s/use-hash
// Modified to check for window existence (for nextjs) before accessing
const useHash = (): string => {
  const [hash, setHash] = React.useState(() => {
    return typeof window === 'undefined' ? '' : window.location.hash;
  });

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const handler = () => {
      setHash(window.location.hash);
    };

    window.addEventListener('hashchange', handler);
    return () => {
      window.removeEventListener('hashchange', handler);
    };
  }, []);

  return hash;
};

//////////////////////
//    PYOBJECT      //
//////////////////////

const PyObject: React.FunctionComponent<{
  module: string;
  object: string;
  method?: string;
  displayText?: string;
  pluralize?: boolean;
  decorator?: boolean;
}> = ({module = 'dagster', object, method, displayText, pluralize = false, decorator = false}) => {
  const value = useContext(SearchIndexContext);
  if (!value) {
    return null;
  }

  const objects = value.objects as any;
  const moduleObjects = objects[module];
  // fifth field is the name of the object
  const objectData =
    moduleObjects &&
    Array.isArray(moduleObjects) &&
    moduleObjects.find(([, , , , name]) => name === object);

  let textValue = displayText || object;
  if (pluralize) {
    textValue += 's';
  }
  if (decorator) {
    textValue = '@' + textValue;
  }
  if (method) {
    textValue += '.' + method;
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
  const link = doc.replace('sections/api/apidocs/', '/_apidocs/');
  const methodSuffix = method ? '.' + method : '';

  return (
    <Link href={link + '#' + module + '.' + object + methodSuffix}>
      <a className="no-underline hover:underline">
        <code className="bg-blue-100 dark:bg-gray-700 p-1">{textValue}</code>
      </a>
    </Link>
  );
};

////////////////////////
//      Callouts      //
///////////////////////

const ADMONITION_STYLES = {
  note: {
    colors: {
      bg: 'primary-100',
      borderIcon: 'primary-500',
      text: 'gray-900',
    },
    icon: Icons.About,
  },
  warning: {
    colors: {bg: 'yellow-50', borderIcon: 'yellow-400', text: 'yellow-700'},
    icon: Icons.About,
  },
};

const Admonition = ({style, children}) => {
  const {colors, icon} = ADMONITION_STYLES[style];
  return (
    <div className={`bg-${colors.bg} border-l-4 border-${colors.borderIcon} p-4 my-4`}>
      <div className="flex">
        {/* Make container for the svg element that aligns it with the top right of the parent flex container */}
        <div className="flex-shrink-0">
          <svg
            className={`mt-.5 h-5 w-5 text-${colors.borderIcon}`}
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 25 25"
            fill="currentColor"
            aria-hidden="true"
          >
            {icon && icon}
          </svg>
        </div>
        <div className="flex-shrink-1 ml-3">
          <div className="admonition">{children}</div>
        </div>
      </div>
    </div>
  );
};

export const Note = ({children}) => {
  return <Admonition style="note">{children}</Admonition>;
};

export const Warning = ({children}) => {
  return <Admonition style="warning">{children}</Admonition>;
};

//////////////////////
//       CHECK      //
//////////////////////

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

//////////////////////
//       CROSS      //
//////////////////////

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

//////////////////////
//    LINKGRID      //
//////////////////////

const LinkGrid = ({children}) => {
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
    .split('')
    .reduce((prevHash, currVal) => ((prevHash << 5) - prevHash + currVal.charCodeAt(0)) | 0, 0);
}

const getColorForString = (s: string) => {
  const colors = [
    ['bg-yellow-100 text-yellow-800'],
    ['bg-green-100 text-green-800'],
    ['bg-blue-100 text-blue-800'],
    ['bg-red-100 text-red-800'],
    ['bg-indigo-100 text-indigo-800'],
    ['bg-pink-100 text-pink-800'],
    ['bg-purple-100 text-purple-800'],
    ['bg-gray-100 text-gray-800'],
  ];

  return colors[Math.abs(hashCode(s)) % colors.length];
};

//////////////////////
//       BADGE      //
//////////////////////

const Badge = ({text}) => {
  const colors = getColorForString(text);
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-sm font-medium ${colors}`}
    >
      {text}
    </span>
  );
};

//////////////////////
//  LINK GRID ITEM  //
//////////////////////

const LinkGridItem = ({title, href, children, tags = []}) => {
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

//////////////////////
//  CODE REF LINK   //
//////////////////////

const CodeReferenceLink = ({filePath, isInline, children}) => {
  const url = `https://github.com/dagster-io/dagster/tree/${LATEST_VERSION}/${filePath}`;

  if (isInline) {
    return <a href={url}>{children}</a>;
  } else {
    return (
      <div className="bg-primary-100 rounded flex item-center p-4">
        <div>
          <svg className="h-8 w-8 text-primary-900" fill="currentColor" viewBox="0 0 24 24">
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

//////////////////////
//    REF TABLE     //
//////////////////////

const ReferenceTable = ({children}) => {
  return (
    <table
      className="table"
      style={{
        width: '100%',
      }}
    >
      <thead>
        <tr>
          <th>Property</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>{children}</tbody>
    </table>
  );
};

const ReferenceTableItem = ({propertyName, children}) => {
  return (
    <tr>
      <td
        style={{
          width: '40%',
        }}
      >
        {propertyName}
      </td>
      <td>{children}</td>
    </tr>
  );
};

const InstanceDiagramBox = ({href = '#', className = '', children}) => {
  return (
    <a
      href={href}
      className={`bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 flex-1 h-16 rounded flex justify-center items-center font-medium ${className}`}
    >
      {children}
    </a>
  );
};

//////////////////////
//       TODO       //
//////////////////////

const TODO = () => {
  return (
    <div className="h-48 w-full bg-red-100 flex justify-center items-center rounded-lg">
      <span className="font-bold">TODO</span>
    </div>
  );
};

////////////////////////
// IMAGE PLACEHOLDER  //
////////////////////////

const PlaceholderImage = ({caption = 'Placeholder Image'}) => {
  return (
    <div className="h-48 w-full bg-gray-100 flex justify-center items-center rounded-lg">
      <span className="font-bold">{caption}</span>
    </div>
  );
};

////////////////////////
// EXPERIMENTAL BADGE //
////////////////////////

const Experimental = () => {
  return (
    <div className="experimental-tag">
      <span className="hidden">(</span>Experimental<span className="hidden">)</span>
    </div>
  );
};

////////////////////////
//  Preview BADGE  //
////////////////////////

const Preview = () => {
  return (
    <div className="preview-tag">
      <span className="hidden">(</span>Preview<span className="hidden">)</span>
    </div>
  );
};

////////////////////////
//  Beta BADGE  //
////////////////////////

const Beta = () => {
  return (
    <div className="beta-tag">
      <span className="hidden">(</span>Beta<span className="hidden">)</span>
    </div>
  );
};

////////////////////////
//  DEPRECATED BADGE  //
////////////////////////

const Deprecated = () => {
  return (
    <div className="deprecated-tag">
      <span className="hidden">(</span>Deprecated<span className="hidden">)</span>
    </div>
  );
};

////////////////////////
//  SUPERSEDED BADGE  //
////////////////////////

const Superseded = () => {
  return (
    <div className="superseded-tag">
      <span className="hidden">(</span>Superseded<span className="hidden">)</span>
    </div>
  );
};

//////////////////////
//  LEGACY BADGE    //
//////////////////////

const Legacy = () => {
  return (
    <div className="legacy-tag">
      <span className="hidden">(</span>Legacy<span className="hidden">)</span>
    </div>
  );
};

// next-mdx converts code blocks to <code> elements wrapped in <pre> elements.
// We need to access the props of the code element to see if we should render an asset
// graph DAG; so we turn the <pre> tag into a styling no-op and create a new <pre> tag
// around the <code> tag once we have access to the <code> tag's props.
const Pre: React.FC<React.HTMLProps<HTMLPreElement>> = ({children, ...props}) => {
  const updatedProps = {...props, className: 'noop'};
  // Add a prop to children so that the Code renderer can tell if it's a code block
  // or not
  return (
    <pre {...updatedProps}>
      {React.Children.map(children, (child: ReactElement<any>) =>
        React.cloneElement(child, {fullwidth: true}),
      )}
    </pre>
  );
};

//////////////////////
//    CODE BLOCKS   //
//////////////////////

interface CodeProps extends React.HTMLProps<HTMLElement> {
  dagimage?: string;
  fullwidth?: boolean;
}

const Code: React.FC<CodeProps> = ({children, dagimage, ...props}) => {
  const preRef = useRef<HTMLPreElement>(null);
  const [copied, setCopied] = useState(false);

  // Early exit if we're not a full width code block
  if (!props.fullwidth) {
    return <code {...props}>{children}</code>;
  }

  const onClick = async () => {
    try {
      await navigator.clipboard.writeText(preRef.current?.innerText);
      setCopied(true);
    } catch (err) {
      console.log('Fail to copy', err);
    }

    setTimeout(() => {
      setCopied(false);
    }, 1000);
  };

  return (
    <div className="relative" style={{display: 'flex'}}>
      <div style={{flex: '1 1 auto', position: 'relative', minWidth: 0}}>
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
        <pre
          className={props.className}
          ref={preRef}
          style={{height: '100%', marginBottom: 0, marginTop: 0}}
        >
          <code {...props}>{children}</code>
        </pre>
      </div>
      {dagimage && (
        <RenderedDAG
          svgSrc={'/' + dagimage}
          mobileImgSrc="/images-2022-july/screenshots/python-assets2.png"
        />
      )}
    </div>
  );
};

//////////////////////
//  ARTICLE LISTS   //
//////////////////////

const ArticleList = ({children}) => {
  return (
    <div className="category-container">
      <div className="category-inner-container">
        <ul
          style={{
            columnCount: 2,
            columnGap: '20px',
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

const ArticleListItem = ({title, href}) => {
  return (
    <li
      style={{
        marginTop: 0,
      }}
    >
      {href.startsWith('http') ? (
        <NextLink href={href} legacyBehavior>
          {title}
        </NextLink>
      ) : (
        <Link href={href}>{title}</Link>
      )}
    </li>
  );
};

//////////////////////
//  EXAMPLE BOXES   //
//////////////////////

const ExampleItemSmall = ({title, tags = []}) => {
  return (
    <button className="w-full h-full py-3 px-4 rounded-lg bg-white border hover:border-gray-500 text-gray-500">
      <span className="font-bold text-gable-green hover:no-underline">{title}</span>
      <div className="mt-2 text-sm space-x-1 space-y-1 bg-opacity-70">
        {tags.map((tag) => (
          <Badge key={tag} text={tag} />
        ))}
      </div>
    </button>
  );
};

const ExampleItem = ({title, hrefDoc = null, hrefCode, children, tags = []}) => {
  return (
    <div className="px-6 py-4 rounded-lg shadow-lg shadow-cyan-500/50 relative group bg-white">
      <span className="font-bold text-2xl text-gable-green">{title}</span>
      <div className="space-x-2 bg-opacity-70">
        {tags.map((tag) => (
          <Badge key={tag} text={tag} />
        ))}
      </div>
      <p className="text-sm text-gray-500">{children}</p>
      <div className="inline-flex flex-row space-x-4">
        <a href={hrefCode}>
          <button className="py-1 px-4 rounded-lg bg-gable-green text-white hover:bg-transparent hover:text-gable-green hover: border hover:border-gable-green">
            View
          </button>
        </a>
        {hrefDoc && (
          <Link href={hrefDoc}>
            <button className="py-1 px-4 rounded-lg bg-transparent border text-gray-500 hover:text-gray-700 hover:bg-gray-100 hover:border-gray-300">
              Guide
            </button>
          </Link>
        )}
      </div>
    </div>
  );
};

//////////////////////
//       TABS       //
//////////////////////

interface TabItem {
  name: string;
  children: any;
}
const TabItem = (_: TabItem) => {}; // container to pass through name and children

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

const TabGroup: React.FC<{children: any; persistentKey?: string}> = ({children, persistentKey}) => {
  const [selectedTab, setSelectedTab] = useState(0);
  const anchor = useHash();

  const [anchorsInChildren, setAnchorsInChildren] = useState<{[anchor: string]: number}>({});
  const handleTabs = useCallback((node: HTMLElement) => {
    if (!node) {
      return;
    }
    const out = {};

    // Once the tabs render, get the list of element IDs and the map to the
    // tab index they are in
    const tabs = node.querySelectorAll("[role='tabpanel']");
    for (let i = 0; i < tabs.length; i++) {
      const tab = tabs[i] as HTMLElement;
      for (const element of tab.querySelectorAll('[id]')) {
        out[element.id] = i;
      }
    }
    setAnchorsInChildren(out);
  }, []);

  useEffect(() => {
    const anchorWithoutHash = anchor.substring(1);
    if (anchorWithoutHash in anchorsInChildren) {
      const tabIdx = anchorsInChildren[anchorWithoutHash];

      // Scroll page to the hash after re-render
      setSelectedTab(tabIdx);
      setTimeout(() => {
        const elem = document.getElementById(anchorWithoutHash);
        elem?.scrollIntoView();
      }, 10);
    }
  }, [anchor, anchorsInChildren]);

  const contents = (
    <>
      <Tab.List className="flex space-x-2 m-2">
        {React.Children.map(children, (child, idx) => {
          return (
            <Tab
              key={idx}
              className={({selected}) =>
                classNames(
                  'w-full py-3 text-sm font-bold leading-5',
                  'focus:outline-none border-gray-200',
                  selected
                    ? 'border-b-2 border-primary-500 text-primary-500 bg-gray-150'
                    : 'border-b hover:border-gray-500 hover:text-gray-700',
                )
              }
            >
              {child?.props?.name}
            </Tab>
          );
        })}
      </Tab.List>
      <Tab.Panels ref={handleTabs}>
        {React.Children.map(children, (child, idx) => {
          // Set unmount={false} to ensure all tabs render (some are hidden)
          // this way we can gather all the ids in the tab group
          return (
            <Tab.Panel key={idx} className={classNames('p-3')} unmount={false}>
              {child.props.children}
            </Tab.Panel>
          );
        })}
      </Tab.Panels>
    </>
  );

  return (
    <div className="w-full px-2 py-2 sm:px-0">
      {persistentKey ? (
        <PersistentTabContext.Consumer>
          {(context) => (
            <Tab.Group
              selectedIndex={context.getTabState(persistentKey)}
              onChange={(idx) => context.setTabState(persistentKey, idx)}
            >
              {contents}
            </Tab.Group>
          )}
        </PersistentTabContext.Consumer>
      ) : (
        <Tab.Group selectedIndex={selectedTab} onChange={(idx) => setSelectedTab(idx)}>
          {contents}
        </Tab.Group>
      )}
    </div>
  );
};

//////////////////////
//      IMAGES      //
//////////////////////

const Image = ({children, ...props}) => {
  /* Only version images when all conditions meet:
   * - use <Image> component in mdx
   * - on non-master version
   * - in public/images/ dir
   */
  const {src} = props;
  if (!src.startsWith('/images/')) {
    return (
      <span className="block mx-auto">
        <NextImage {...(props as any)} />
      </span>
    );
  }
  return (
    <Zoom wrapElement="span" wrapStyle={{display: 'block'}}>
      <span className="block mx-auto">
        <NextImage src={src} width={props.width} height={props.height} alt={props.alt} />
      </span>
    </Zoom>
  );
};

//////////////////////
//     BUTTONS      //
//////////////////////

const Button = ({
  children,
  link,
  style = 'primary',
}: {
  children: any;
  link: string;
  style?: 'primary' | 'secondary' | 'blurple';
  icon: string;
}) => {
  return (
    <a
      href={link}
      className={cx(
        'text-sm lg:text-base select-none text-center py-2 px-4 rounded-xl transition hover:no-underline cursor-pointer',
        style === 'primary' && 'bg-gable-green text-white hover:bg-gable-green-darker',
        style === 'secondary' &&
          'border text-gable-green hover:text-gable-green-darker hover:border-gable-green',
        style === 'blurple' && 'bg-blurple text-white hover:bg-blurple-darker',
      )}
    >
      <div className="h-full flex flex-1 flex-col justify-evenly align-center">{children}</div>
    </a>
  );
};

export default {
  a: ({children, ...props}) => {
    // Skip in-page links and external links
    if (!props.href.startsWith('/')) {
      return <a {...props}>{children}</a>;
    }
    // Hydrate the links in raw MDX to include versions
    return (
      <Link href={props.href}>
        <a {...props}> {children}</a>
      </Link>
    );
  },
  img: ({children, ...props}) => (
    <span className="block mx-auto">
      <img {...(props as any)} />
    </span>
  ),
  code: Code,
  pre: Pre,
  PyObject,
  Link,
  Check,
  Cross,
  Image,
  LinkGrid,
  LinkGridItem,
  Note,
  Button,
  Warning,
  CodeReferenceLink,
  InstanceDiagramBox,
  TODO,
  PlaceholderImage,
  Experimental,
  Deprecated,
  Superseded,
  Preview,
  Beta,
  Legacy,
  Icons,
  ReferenceTable,
  ReferenceTableItem,
  DagsterVersion,
  DagsterDevTabs,
  StructuredEventLogs,
  ExperimentalCallout,
  RawComputeLogs,
  AddGitlabVariable,
  AddGitubRepositorySecret,
  ApplicableCloudPlan,
  ApplicableDagsterProduct,
  AssetCheckAlerts,
  GenerateAgentToken,
  ScimSupportedFeatures,
  BDCreateConfigureAgent,
  DbtModelAssetExplanation,
  EnvironmentVariablesIntro,
  EnvVarsBenefits,
  K8sEnvVarsConfiguration,
  DockerEnvVarsConfiguration,
  AmazonEcsEnvVarsConfiguration,
  ArticleList,
  ArticleListItem,
  ExampleItemSmall,
  ExampleItem,
  TabGroup,
  TabItem,
  RenderedDAG,
};
