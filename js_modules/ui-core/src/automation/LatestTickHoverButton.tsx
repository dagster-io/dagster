import {
  Box,
  Button,
  ButtonLink,
  Caption,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  HoverButton,
  Icon,
  Popover,
  Spinner,
} from '@dagster-io/ui-components';
import {ReactNode, useState} from 'react';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {Timestamp} from '../app/time/Timestamp';
import {InstigationTickStatus} from '../graphql/types';
import {TickTagFragment} from '../instigation/types/InstigationTick.types';
import {numberFormatter} from '../ui/formatters';
import styles from './css/LatestTickHoverButton.module.css';

interface Props {
  tick: TickTagFragment | null;
}

export const LatestTickHoverButton = ({tick}: Props) => {
  const [showErrors, setShowErrors] = useState(false);

  const content = () => {
    if (!tick) {
      return (
        <Box padding={{vertical: 8, horizontal: 12}}>
          <Caption>No ticks yet</Caption>
        </Box>
      );
    }

    const icon = statusToIcon[tick.status];
    const timestamp = <Timestamp timestamp={{unix: tick.timestamp}} />;

    switch (tick.status) {
      case InstigationTickStatus.FAILURE:
        return (
          <HoverContent
            icon={icon}
            title="Latest tick failed"
            timestamp={timestamp}
            content={
              <div>
                {tick.error ? (
                  <ButtonLink onClick={() => setShowErrors(true)}>Show error</ButtonLink>
                ) : (
                  'Unknown error'
                )}
              </div>
            }
          />
        );
      case InstigationTickStatus.SUCCESS: {
        const runCount = tick.runIds.length;
        return (
          <HoverContent
            icon={icon}
            title="Latest tick succeeded"
            timestamp={timestamp}
            content={
              <div>
                {runCount === 1
                  ? '1 run requested'
                  : `${numberFormatter.format(runCount)} runs requested`}
              </div>
            }
          />
        );
      }
      case InstigationTickStatus.STARTED:
        return <HoverContent icon={icon} title="Evaluating tick" timestamp={timestamp} />;
      case InstigationTickStatus.SKIPPED:
      default:
        return (
          <HoverContent
            icon={icon}
            title="Latest tick skipped"
            timestamp={timestamp}
            content={<Caption>{tick.skipReason ?? 'No reason provided'}</Caption>}
          />
        );
    }
  };

  return (
    <>
      <Popover content={content()} placement="top" interactionKind="hover">
        <HoverButton>
          {tick ? statusToIcon[tick.status] : <Icon name="missing" color={Colors.accentGray()} />}
        </HoverButton>
      </Popover>
      {tick?.error ? (
        <Dialog isOpen={showErrors} title="Error" style={{width: '80vw'}}>
          <DialogBody>
            <PythonErrorInfo error={tick.error} />
          </DialogBody>
          <DialogFooter topBorder>
            <Button
              intent="primary"
              onClick={() => {
                setShowErrors(false);
              }}
            >
              Done
            </Button>
          </DialogFooter>
        </Dialog>
      ) : null}
    </>
  );
};

const statusToIcon: Record<InstigationTickStatus, ReactNode> = {
  [InstigationTickStatus.FAILURE]: <Icon name="warning" color={Colors.accentYellow()} />,
  [InstigationTickStatus.SUCCESS]: <Icon name="done" color={Colors.accentGreen()} />,
  [InstigationTickStatus.STARTED]: <Spinner purpose="body-text" />,
  [InstigationTickStatus.SKIPPED]: <Icon name="status" color={Colors.accentGray()} />,
};

interface HoverContentProps {
  icon: ReactNode;
  title: ReactNode;
  timestamp: ReactNode;
  content?: ReactNode;
}

const HoverContent = ({icon, title, timestamp, content}: HoverContentProps) => {
  return (
    <Box padding={12} className={styles.hoverContent}>
      <Box
        border={content ? 'bottom' : undefined}
        padding={content ? {bottom: 12} : undefined}
        margin={content ? {bottom: 8} : undefined}
        flex={{
          direction: 'row',
          alignItems: 'center',
          gap: 8,
          justifyContent: 'space-between',
        }}
      >
        <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
          {icon}
          <div>{title}</div>
        </Box>
        <div>{timestamp}</div>
      </Box>
      {content ? <div>{content}</div> : null}
    </Box>
  );
};
