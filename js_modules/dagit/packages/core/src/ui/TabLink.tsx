import {TabStyleProps, getTabA11yProps, getTabContent, tabCSS} from '@dagster-io/ui';
import * as React from 'react';
import {Link, LinkProps} from 'react-router-dom';
import styled from 'styled-components/macro';

interface TabLinkProps extends TabStyleProps, Omit<LinkProps, 'title'> {
  title?: React.ReactNode;
}

export const TabLink = styled((props: TabLinkProps) => {
  const {to, title, ...rest} = props;
  const containerProps = getTabA11yProps(props);
  const content = getTabContent(props);

  const titleText = typeof title === 'string' ? title : undefined;

  return (
    <Link to={to} title={titleText} {...containerProps} {...rest}>
      {content}
    </Link>
  );
})<TabLinkProps>`
  ${tabCSS}
`;
