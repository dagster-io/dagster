import {Alert, Box, Colors, Tab, Table, Tabs} from '@dagster-io/ui-components';
import {BorderSide} from '@dagster-io/ui-components/src/components/types';
import clsx from 'clsx';
import {DetailedHTMLProps, HTMLAttributes, useLayoutEffect, useRef, useState} from 'react';
import {Components} from 'react-markdown/lib/ast-to-react';

import {CopyIconButton} from '../ui/CopyButton';
import styles from './css/MarkdownSupport.module.css';
import {IntegrationFrontmatter} from './types';

const DOCS_ORIGIN = 'https://docs.dagster.io';

/**
 * On the docs site, we render Markdown using Docasaurus, which supports GFM (the
 * Github extensions), partials, directives, and freeform embedded React components. (MDX)
 *
 * The generate.ts script that pre-processes the docs markdown for the marketplace API
 * removes MDX partials and converts <CodeExample file={...} /> to code blocks with inline
 * content, since the referenced files would be unavailable in the app.
 *
 * We can't execute inline JSX within the markdown because it would require parsing JSX and
 * then evaling the code. However, we can use `rehype-raw` to parse the inline components
 * as HTML, and then register React components with `ast-to-react` to be used to render
 * those HTML tags.
 *
 * This is lightweight and works well for our use case, but there are a few subtle gotchas:
 *
 * - `<PyObject decorator />` yields a `decorator=true` prop in JSX but below we get
 *   `decorator=''` because the "props" these components receive are HTML attributes.
 *
 * - Childless nodes like `<Beta />` are passed the subsequent nodes as children and we
 *   need to use a fragment to render them. This seems to be a behavior of rehype-raw.
 *
 * In general, we're trying to make this markdown match the app (eg: same table styling,
 * same tabs) instead of styling it to be identical to the docs.
 *
 */
export const MDXAnchor: Components['a'] = (props) => {
  const {children, href, ...rest} = props;
  const finalHref = href?.startsWith('/') ? `${DOCS_ORIGIN}${href}` : href;
  return (
    <a href={finalHref} target="_blank" rel="noreferrer" {...rest}>
      {children}
    </a>
  );
};

export const MDXCode = (
  props: DetailedHTMLProps<HTMLAttributes<HTMLElement>, any> & {inline?: boolean},
) => {
  const {children, className, inline, ...rest} = props;

  const codeRef = useRef<HTMLElement>(null);
  const [value, setValue] = useState('');

  useLayoutEffect(() => {
    setValue(codeRef.current?.textContent?.trim() ?? '');
  }, [children]);

  if (inline) {
    return (
      <code className={clsx(className, styles.inlineCode)} {...rest}>
        {children}
      </code>
    );
  }

  return (
    <div className={styles.codeBlock}>
      <code className={className} {...rest} ref={codeRef}>
        {children}
      </code>
      <div className={styles.copyButton}>
        <CopyIconButton value={value} iconSize={16} iconColor={Colors.accentPrimary()} />
      </div>
    </div>
  );
};

export const MDXBeta = ({children}: {children: React.ReactNode}) => (
  <>
    <Alert
      intent="warning"
      title="Warning"
      description="This feature is considered in a beta stage. It is still being tested and may change."
    />
    {children}
  </>
);

export const MDXDeprecated = ({children}: {children: React.ReactNode}) => (
  <>
    <Alert
      intent="warning"
      title="Warning"
      description="This feature is considered deprecated and is still available, but will be removed in the future. It is recommended to avoid new usage."
    />
    {children}
  </>
);

export const MDXTabs = ({
  children,
  border = 'bottom',
}: {
  children: React.ReactNode;
  border?: BorderSide | null;
}) => {
  const [tabId, setTabId] = useState<string | null>(null);

  const tabitems: React.ReactElement<{value: string}>[] = (
    Array.isArray(children) ? children : [children]
  ).filter(
    (node) => node && typeof node === 'object' && 'type' in node && node.type === MDXTabItem,
  );

  const selected = tabitems.find((t) => t.props.value === tabId) || tabitems[0];

  return (
    <Box
      background={Colors.backgroundLight()}
      padding={{horizontal: 20, bottom: 12}}
      style={{borderRadius: 8}}
    >
      <Box border={border} padding={{left: 8}}>
        <Tabs selectedTabId={selected?.props.value} onChange={setTabId}>
          {tabitems.map((t) => (
            <Tab key={t.props.value} id={t.props.value} title={t.props.value} />
          ))}
        </Tabs>
      </Box>
      {selected ? (
        <div role="tabpanel" key={selected.props.value}>
          {selected}
        </div>
      ) : null}
    </Box>
  );
};

export const MDXTabItem = ({children}: {value: string; children: React.ReactNode}) => {
  return children;
};

export const MDXPyObject = ({
  section,
  object,
  displayText,
  module = 'dagster',
  pluralize,
  decorator,
  children,
}: {
  section: string;
  module: string;
  object: string;
  displayText?: string;
  pluralize?: boolean;
  decorator?: boolean;
  children?: React.ReactNode;
}) => {
  let textValue = displayText || object;
  if (pluralize !== undefined) {
    textValue += 's';
  }

  if (decorator !== undefined) {
    if (module === 'dagster') {
      textValue = '@dg.' + textValue;
    } else {
      textValue = '@' + module + '.' + textValue;
    }
  }

  let href = `/api/dagster/${section}#${module}.${object}`;
  if (section === 'libraries' || section === 'dagster_dg') {
    const _package = module.replace(/_/g, '-');
    href = `/api/${section}/${_package}#${module}.${object}`;
  }

  return (
    <>
      <a href={`${DOCS_ORIGIN}${href}`} target="_blank" rel="noreferrer">
        <code className={styles.inlineCode} style={{paddingLeft: '4px', paddingRight: '4px'}}>
          {textValue}
        </code>
      </a>
      {children}
    </>
  );
};

const MDXPackageInstallInstructions = ({
  packagename,
  children,
}: {
  packagename: string;
  children: React.ReactNode;
}) => {
  const uvCommand = `uv add ${packagename}`;
  const pipCommand = `pip install ${packagename}`;

  return (
    <>
      <MDXTabs border={null}>
        <MDXTabItem value="uv">
          <MDXCode>{uvCommand}</MDXCode>
        </MDXTabItem>
        <MDXTabItem value="pip">
          <MDXCode>{pipCommand}</MDXCode>
        </MDXTabItem>
      </MDXTabs>
      {children}
    </>
  );
};

/** In Docasaurus and MDX, expressions like `{frontMatter.description}` are JS-interpreted,
 * so you can do a full range of things like `{1 + 1}`. We don't want to allow `eval` and only
 * need basic support for referencing frontmatter, so we implement it via a trivial regexp instead.
 */
export function replaceFrontmatterExpressions(
  content: string,
  frontmatter: IntegrationFrontmatter,
): string {
  let transformed = content;
  Object.entries(frontmatter).forEach(([key, value]) => {
    transformed = transformed.replace(
      new RegExp(`\\{frontMatter\\.${key}\\}`, 'gi'),
      `${value ?? ''}`,
    );
  });
  return transformed;
}

export function prependInstallationSection(content: string, frontmatter: IntegrationFrontmatter) {
  // If an install section exists or if our MDX component is in use, don't make adjustments.
  if (/# ?Install/i.test(content) || content.includes('PackageInstallInstructions')) {
    return content;
  }

  // Option 1: If an explicit installation command is listed, display it
  if (frontmatter.installationCommand) {
    return `## Installation\n\n\`\`\`\n${frontmatter.installationCommand}\n\`\`\`\n\n${content}`;
  }

  // Option 2: If a pypi package name is provided, display pip and uv install instructions
  const packageName = frontmatter.pypi ? packageNameFromPypi(frontmatter.pypi) : null;
  if (packageName) {
    return `## Installation\n\n<PackageInstallInstructions packageName="${packageName}" />\n\n${content}`;
  }

  return content;
}

function packageNameFromPypi(pypiUrl: string) {
  const match = /pypi\.org\/project\/([^\/]+)\/?/.exec(pypiUrl);
  return match ? match[1] : null;
}

export const MDXComponents = {
  beta: MDXBeta,
  deprecated: MDXDeprecated,
  packageinstallinstructions: MDXPackageInstallInstructions,
  pyobject: MDXPyObject,
  table: Table,
  code: MDXCode,
  tabs: MDXTabs,
  tabitem: MDXTabItem,
  a: MDXAnchor,
  // h1: MDXH1,
  // h2: MDXH2,
} as Components;
