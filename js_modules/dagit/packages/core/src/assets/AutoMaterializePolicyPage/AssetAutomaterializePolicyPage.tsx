import {Box, ButtonLink, Colors, Dialog, Icon, Subheading, Tag, Tooltip} from '@dagster-io/ui';
import dayjs from 'dayjs';
import LocalizedFormat from 'dayjs/plugin/localizedFormat';
import React from 'react';
import styled from 'styled-components/macro';

import {RunStatus} from '../../graphql/types';
import {RunStatusIndicator} from '../../runs/RunStatusDots';
import {useFilters} from '../../ui/Filters';

dayjs.extend(LocalizedFormat);

export const AssetAutomaterializePolicyPage = () => {
  const {button} = useFilters({filters: []});
  return (
    <Box flex={{direction: 'row', grow: 1}} style={{color: Colors.Gray700}}>
      <Box
        flex={{direction: 'column', grow: 1}}
        border={{side: 'right', width: 1, color: Colors.KeylineGray}}
      >
        <CenterAlignedRow
          flex={{justifyContent: 'space-between'}}
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <Subheading>Evaluation History</Subheading>
          {button}
        </CenterAlignedRow>
        <Box flex={{grow: 1, direction: 'row'}}>
          <Box
            border={{side: 'right', color: Colors.KeylineGray, width: 1}}
            style={{width: '294px'}}
          >
            <LeftPanel />
          </Box>
          <Box flex={{grow: 1}}>
            <MiddlePanel />
          </Box>
        </Box>
      </Box>
      <Box>
        <RightPanel />
      </Box>
    </Box>
  );
};

const LeftPanel = () => {
  const evaluations = generateMockEvaluations();

  return (
    <Box flex={{direction: 'column'}}>
      {evaluations.map((evaluation) => {
        const date = dayjs.unix(evaluation.date);
        const formattedDate = date.format('lll');
        return (
          <CenterAlignedRow
            flex={{justifyContent: 'space-between'}}
            key={evaluation.date + ''}
            padding={{horizontal: 24, vertical: 8}}
            border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
          >
            {formattedDate}
            {evaluation.materialized ? (
              <Icon name="auto_materialize_policy" size={24} />
            ) : (
              <div
                style={{borderRadius: '50%', height: '10px', width: '10px', color: Colors.Yellow50}}
              />
            )}
          </CenterAlignedRow>
        );
      })}
    </Box>
  );
};

const RightPanel = () => {
  return (
    <Box flex={{direction: 'column'}} style={{maxWidth: '294px'}}>
      <Box
        padding={{vertical: 16, horizontal: 24}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <Subheading>Overview</Subheading>
      </Box>
      <RightPanelSection title="Auto-materialize Policy">
        <RightPanelDetail
          title="On missing"
          value={<Green700Text>True</Green700Text>}
          tooltip="test"
        />
        <RightPanelDetail
          title="On upstream data"
          value={<Green700Text>True</Green700Text>}
          tooltip="test"
        />
        <RightPanelDetail
          title="For freshness"
          value={<Green700Text>True</Green700Text>}
          tooltip="test"
        />
        <RightPanelDetail title="Maximum materializations per hour" value={2} tooltip="test" />
      </RightPanelSection>
      <RightPanelSection title="Freshness Policy">
        <RightPanelDetail title="Maximum lag minutes" tooltip="test" value={2} />
        <Box flex={{direction: 'column', gap: 8}}>
          This asset will be considered late if it is not materialized within 2 minutes of it’s
          upstream dependencies.
          <ButtonLink>View upstream assets</ButtonLink>
        </Box>
      </RightPanelSection>
    </Box>
  );
};

const RightPanelSection = ({
  title,
  children,
}: {
  title: React.ReactNode;
  children: React.ReactNode;
}) => {
  return (
    <Box
      flex={{direction: 'column', gap: 12}}
      border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      padding={{vertical: 12, horizontal: 16}}
    >
      <Subheading>{title}</Subheading>
      {children}
    </Box>
  );
};

const RightPanelDetail = ({
  title,
  tooltip,
  value,
}: {
  title: React.ReactNode;
  tooltip?: React.ReactNode;
  value: React.ReactNode;
}) => {
  return (
    <Box flex={{direction: 'column', gap: 2}}>
      <CenterAlignedRow flex={{gap: 6}}>
        {title}{' '}
        <Tooltip content={<>{tooltip}</>} position="top">
          <Icon name="info" />
        </Tooltip>
      </CenterAlignedRow>
      {value}
    </Box>
  );
};

const MiddlePanel = () => {
  return (
    <Box flex={{direction: 'column', grow: 1}}>
      <CollapsibleSection
        header="Result"
        headerRightSide={
          <>
            <Tag intent="primary">1 Run Requested</Tag>
            <Tag intent="success">
              <CenterAlignedRow flex={{gap: 4}}>
                <RunStatusIndicator status={RunStatus.SUCCESS} size={10} />
                58ab025
              </CenterAlignedRow>
            </Tag>
          </>
        }
      >
        Launched a run to materialize this asset because an upstream asset, transactions_raw, has
        changed since its latest materialization.
      </CollapsibleSection>
      <CollapsibleSection header="Materialization conditions met">
        <Box flex={{direction: 'column', gap: 8}}>
          <Condition text="Materialization is missing" met={false} />
          <Condition text="Code version has changed since latest materialization" met={false} />
          <Condition
            text="Upstream code version has changed since latest materialization"
            met={false}
          />
          <Condition text="Upstream data has changed since latest materialization" met={true} />
          <Condition text="Required to meet a freshness policy" met={false} />
          <Condition text="Required to meet a downstream freshness policy" met={false} />
        </Box>
      </CollapsibleSection>
      <CollapsibleSection header="Skip conditions met">
        <Box flex={{direction: 'column', gap: 8}}>
          <Condition text="Waiting on upstream data" met={false} />
          <Condition text="Exceeds 2 materializations per hour" met={false} />
        </Box>
      </CollapsibleSection>
    </Box>
  );
};

const CollapsibleSection = ({
  header,
  headerRightSide,
  children,
}: {
  header: React.ReactNode;
  headerRightSide?: React.ReactNode;
  children: React.ReactNode;
}) => {
  const [isCollapsed, setIsCollapsed] = React.useState(false);

  return (
    <Box
      flex={{direction: 'column'}}
      border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
    >
      <CenterAlignedRow
        flex={{
          justifyContent: 'space-between',
          gap: 12,
          grow: 1,
        }}
        padding={{vertical: 8, horizontal: 24}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <CenterAlignedRow
          flex={{gap: 8, grow: 1}}
          onClick={() => {
            setIsCollapsed(!isCollapsed);
          }}
          style={{cursor: 'pointer', outline: 'none'}}
          tabIndex={0}
        >
          <Icon
            name="arrow_drop_down"
            style={{transform: isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)'}}
          />
          <Subheading>{header}</Subheading>
        </CenterAlignedRow>
        {headerRightSide}
      </CenterAlignedRow>
      {isCollapsed ? null : <Box padding={{vertical: 12, horizontal: 24}}>{children}</Box>}
    </Box>
  );
};

const Green700Text = styled.div`
  color: ${Colors.Green700};
`;

const Condition = ({
  text,
  met,
  details,
}: {
  text: React.ReactNode;
  met: boolean;
  details?: React.ReactNode;
}) => {
  const [isDetailsDialogOpen, setIsDetailsDialogOpen] = React.useState(false);
  return (
    <CenterAlignedRow flex={{justifyContent: 'space-between'}}>
      <CenterAlignedRow flex={{gap: 8}}>
        <Icon name={met ? 'done' : 'close'} color={met ? Colors.Green700 : Colors.Gray400} />
        <div style={{color: met ? Colors.Green700 : undefined}}>{text}</div>
      </CenterAlignedRow>
      <div>
        {met ? (
          <ButtonLink
            onClick={() => {
              setIsDetailsDialogOpen(true);
            }}
          >
            View details
          </ButtonLink>
        ) : (
          '-'
        )}
      </div>
      <Dialog isOpen={details ? isDetailsDialogOpen : false}>{details}</Dialog>
    </CenterAlignedRow>
  );
};

const CenterAlignedRow = React.forwardRef((props: React.ComponentProps<typeof Box>, ref) => {
  return (
    <Box
      {...props}
      ref={ref}
      flex={{
        direction: 'row',
        alignItems: 'center',
        ...(props.flex || {}),
      }}
    />
  );
});

function generateMockEvaluations() {
  const startDate = new Date('2023-04-27T00:00:00');
  const data = [];

  for (let i = 0; i < 20; i++) {
    const date = new Date(startDate.getTime() + i * 60 * 1000); // Add 1 minute for each iteration
    const unixTimestamp = Math.floor(date.getTime() / 1000); // Convert to Unix timestamp
    const materialized = Math.random() < 0.5; // Randomly assign true or false

    data.push({
      date: unixTimestamp,
      materialized,
    });
  }

  return data;
}
