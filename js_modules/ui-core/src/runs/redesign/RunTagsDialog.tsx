import {
  Button,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  DialogHeader,
  Icon,
  Table,
  Tag,
  Text,
  Tooltip,
} from '@dagster-io/ui-components';

import {RunIDCell} from './RunIDCell';
import {buildTagMap} from './buildTagMap';
import styles from './css/RunTagsDialog.module.css';
import {getPartitionLabel} from './getPartitionLabel';
import {MappedRun} from './mapRunsFeedData';
import {showCopySuccessToast} from './showCopySuccessToast';
import {useCopyToClipboard} from '../../app/browser';
import {tagsAsYamlString} from '../RunTags';

type RunTagsDialogProps = {
  run: MappedRun;
  onClose: () => void;
};

export const RunTagsDialog = ({run, onClose}: RunTagsDialogProps) => {
  const tags = [...run.tags].sort((a, b) => a.key.localeCompare(b.key));
  const partitionLabel = getPartitionLabel(buildTagMap(tags));
  const copy = useCopyToClipboard();

  return (
    <Dialog isOpen onClose={onClose} style={{width: '80vw', maxWidth: 1200, minWidth: 600}}>
      <DialogHeader
        icon="tag"
        label="Tags"
        right={
          <>
            {partitionLabel !== null && <Tag icon="partition">{partitionLabel}</Tag>}
            <RunIDCell entry={run} />
          </>
        }
      />
      <DialogBody>
        <Table compact style={{borderRight: `1px solid ${Colors.keylineDefault()}`}}>
          <thead>
            <tr>
              <th>Key</th>
              <th>Value</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tags.map(({key, value}) => (
              <tr key={key}>
                <td>
                  <Text family="mono" size={14} color="textLight">
                    {key}
                  </Text>
                </td>
                <td>
                  <Text family="mono" size={14} className={styles.value}>
                    {value}
                  </Text>
                </td>
                <td className={styles.actions}>
                  <Tooltip content="Copy tag">
                    <Button
                      intent="none"
                      icon={<Icon name="content_copy" />}
                      aria-label="Copy tag"
                      onClick={() => {
                        copy(`${key}: ${value}`);
                        showCopySuccessToast('Tag copied');
                      }}
                    />
                  </Tooltip>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </DialogBody>
      <DialogFooter topBorder>
        <Button
          icon={<Icon name="content_copy" />}
          onClick={() => {
            copy(tagsAsYamlString(tags));
            showCopySuccessToast('All tags copied');
          }}
        >
          Copy all
        </Button>
        <Button intent="primary" onClick={onClose}>
          Close
        </Button>
      </DialogFooter>
    </Dialog>
  );
};
