import {useState} from 'react';

import {BreadcrumbProps, Breadcrumbs} from '../Breadcrumbs';
import {Colors} from '../Color';
import {MiddleTruncate} from '../MiddleTruncate';
import {Slider} from '../Slider';
import {Heading} from '../Typography';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Breadcrumbs',
  component: Breadcrumbs,
};

const simpleBreadcrumbs: BreadcrumbProps[] = [
  {text: 'Home', href: '#'},
  {text: 'Projects', href: '#'},
  {text: 'dagster-io/dagster', href: '#'},
];

export const Simple = () => {
  return <Breadcrumbs items={simpleBreadcrumbs} />;
};

export const WithCurrentRenderer = () => {
  return (
    <Breadcrumbs
      items={simpleBreadcrumbs}
      currentBreadcrumbRenderer={({text}) => (
        <Heading size={20} weight={500}>
          {text}
        </Heading>
      )}
    />
  );
};

export const WithOnClick = () => {
  const [clicked, setClicked] = useState('(none)');
  const items: BreadcrumbProps[] = [
    {text: 'Root', onClick: () => setClicked('Root')},
    {text: 'Parent', onClick: () => setClicked('Parent')},
    {text: 'Current'},
  ];

  return (
    <div>
      <Breadcrumbs items={items} currentBreadcrumbRenderer={({text}) => <strong>{text}</strong>} />
      <p style={{marginTop: 12}}>Last clicked: {clicked}</p>
    </div>
  );
};

const deepBreadcrumbs: BreadcrumbProps[] = [
  {text: 'Assets', href: '#'},
  {text: 's3', href: '#'},
  {text: 'superdomain_1', href: '#'},
  {text: 'subdomain_1', href: '#'},
  {text: 'subsubdomain_that_is_very_long', href: '#'},
  {text: 'another_deep_level', href: '#'},
  {text: 'my_asset', href: '#'},
];

export const OverflowCollapse = () => {
  const [width, setWidth] = useState(400);

  return (
    <>
      <Slider min={200} max={800} step={10} value={width} onChange={setWidth} />
      <div
        style={{width, border: `1px solid ${Colors.borderDefault()}`, padding: 8, marginTop: 12}}
      >
        <Breadcrumbs items={deepBreadcrumbs} />
      </div>
    </>
  );
};

export const OverflowWithCustomRenderers = () => {
  const [width, setWidth] = useState(500);

  return (
    <>
      <Slider min={200} max={800} step={10} value={width} onChange={setWidth} />
      <div style={{width, marginTop: 12}}>
        <Breadcrumbs
          items={deepBreadcrumbs}
          currentBreadcrumbRenderer={({text}) => (
            <Heading size={20} weight={500} style={{maxWidth: 200, overflow: 'hidden'}}>
              {typeof text === 'string' ? <MiddleTruncate text={text} /> : text}
            </Heading>
          )}
          breadcrumbRenderer={({text, href}) => (
            <a href={href} style={{maxWidth: 150, overflow: 'hidden', display: 'block'}}>
              {typeof text === 'string' ? <MiddleTruncate text={text} /> : text}
            </a>
          )}
        />
      </div>
    </>
  );
};

export const OverflowMenuVisible = () => {
  return (
    <div style={{width: 200, border: `1px solid ${Colors.borderDefault()}`, padding: 8}}>
      <Breadcrumbs
        items={deepBreadcrumbs}
        currentBreadcrumbRenderer={({text}) => <strong>{text}</strong>}
      />
    </div>
  );
};

export const TwoItems = () => {
  const items: BreadcrumbProps[] = [{text: 'Home', href: '#'}, {text: 'Current Page'}];
  return <Breadcrumbs items={items} />;
};

export const SingleItem = () => {
  const items: BreadcrumbProps[] = [{text: 'Only Item'}];
  return (
    <Breadcrumbs
      items={items}
      currentBreadcrumbRenderer={({text}) => (
        <Heading size={20} weight={500}>
          {text}
        </Heading>
      )}
    />
  );
};
