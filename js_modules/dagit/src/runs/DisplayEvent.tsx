import {Tag} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../CustomAlertProvider';
import {copyValue} from '../DomUtils';
import {IStepDisplayEvent} from '../RunMetadataProvider';

interface DisplayEventProps {
  event: IStepDisplayEvent;
}

const DisplayEventItem: React.FunctionComponent<IStepDisplayEvent['items'][0]> = ({
  action,
  actionText,
  actionValue,
  text,
}) => {
  let actionEl: React.ReactNode = actionText;

  if (action === 'copy') {
    actionEl = (
      <DisplayEventLink title={'Copy to clipboard'} onClick={(e) => copyValue(e, actionValue)}>
        {actionText}
      </DisplayEventLink>
    );
  }
  if (action === 'open-in-tab') {
    actionEl = (
      <DisplayEventLink href={actionValue} title={`Open in a new tab`} target="__blank">
        {actionText}
      </DisplayEventLink>
    );
  }
  if (action === 'show-in-modal') {
    actionEl = (
      <DisplayEventLink
        title="Show full value"
        onClick={() =>
          showCustomAlert({
            body: <div style={{whiteSpace: 'pre-wrap'}}>{actionValue}</div>,
            title: 'Value',
          })
        }
      >
        {actionText}
      </DisplayEventLink>
    );
  }
  return (
    <DisplayEventItemContainer>
      {text}: {actionEl}
    </DisplayEventItemContainer>
  );
};

export const DisplayEvent: React.FunctionComponent<DisplayEventProps> = ({event}) => (
  <DisplayEventContainer>
    <LabelColumn>
      {'status' in event
        ? IconComponents[(event as any).icon]('Expectation')
        : IconComponents[event.icon]('Materialization')}
      {event.text}
    </LabelColumn>
    {event.items.map((item, idx) => (
      <DisplayEventItem {...item} key={idx} />
    ))}
  </DisplayEventContainer>
);

const DisplayEventContainer = styled.div`
  white-space: pre-wrap;
  font-size: 12px;
`;

const LabelColumn = styled.div`
  display: flex;
  align-items: baseline;
  font-weight: 500;
`;

const DisplayEventItemContainer = styled.div`
  display: block;
  padding-left: 15px;
`;

const DisplayEventLink = styled.a`
  text-decoration: underline;
  color: inherit;
  &:hover {
    color: inherit;
  }
`;

const IconComponents: {[key: string]: (word: string) => React.ReactNode} = {
  'dot-success': (word: string) => (
    <Tag minimal={true} intent={'success'} style={{marginRight: 4}}>
      {word}
    </Tag>
  ),
  'dot-failure': (word: string) => (
    <Tag minimal={true} intent={'danger'} style={{marginRight: 4}}>
      {word}
    </Tag>
  ),
  'dot-pending': (word: string) => (
    <Tag minimal={true} intent={'none'} style={{marginRight: 4}}>
      {word}
    </Tag>
  ),
  none: (word: string) => (
    <Tag minimal={true} intent={'none'} style={{marginRight: 4}}>
      {word}
    </Tag>
  ),
  file: () => (
    <img
      style={{flexShrink: 0, alignSelf: 'center'}}
      src={require('../images/icon-file.svg')}
      alt="file icon"
    />
  ),
  link: () => (
    <img
      style={{flexShrink: 0, alignSelf: 'center'}}
      src={require('../images/icon-link.svg')}
      alt="link icon"
    />
  ),
};
