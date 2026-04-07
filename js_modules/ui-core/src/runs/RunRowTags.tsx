import {
  Button,
  ButtonLink,
  Caption,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
} from '@dagster-io/ui-components';
import * as React from 'react';

import {DagsterTag, TagType} from './RunTag';
import {RunTags, tagsAsYamlString} from './RunTags';
import {getBackfillPath} from './RunsFeedUtils';
import {RunFilterToken} from './RunsFilterInput';
import {RunTableRunFragment} from './types/RunTableRunFragment.types';
import {useTagPinning} from './useTagPinning';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {CopyButton} from '../ui/CopyButton';
import styles from './css/RunRowTags.module.css';

export const RunRowTags = ({
  run,
  onAddTag,
  isHovered,
  hideTags,
}: {
  run: Pick<RunTableRunFragment, 'tags' | 'assetSelection' | 'mode'>;
  onAddTag?: (token: RunFilterToken) => void;
  isHovered: boolean;
  hideTags?: string[];
}) => {
  const {isTagPinned, onToggleTagPin} = useTagPinning();
  const [showRunTags, setShowRunTags] = React.useState(false);

  const allTagsWithPinned = React.useMemo(() => {
    const allTags: {key: string; value: string}[] = [...run.tags];
    if (run.mode !== 'default') {
      allTags.push({key: 'mode', value: run.mode});
    }
    return allTags.map((tag) => {
      return {...tag, pinned: isTagPinned(tag)};
    });
  }, [run, isTagPinned]);

  const tagsToShow = React.useMemo(() => {
    const targetBackfill = allTagsWithPinned.find((tag) => tag.key === DagsterTag.Backfill);
    const tagKeys: Set<string> = new Set([]);
    const tags: TagType[] = [];

    if (targetBackfill && targetBackfill.pinned && !hideTags?.includes(DagsterTag.Backfill)) {
      const link = getBackfillPath(targetBackfill.value);
      tags.push({
        ...targetBackfill,
        link,
      });
      tagKeys.add(DagsterTag.Backfill as string);
    }
    allTagsWithPinned.forEach((tag) => {
      if (tagKeys.has(tag.key)) {
        // We already added this tag
        return;
      }
      if (hideTags?.includes(tag.key)) {
        return;
      }
      if (tag.pinned) {
        tags.push(tag);
      }
    });
    return tags;
  }, [allTagsWithPinned, hideTags]);

  return (
    <>
      <div className={styles.runTagsWrapper}>
        {tagsToShow.length ? (
          <RunTags tags={tagsToShow} onAddTag={onAddTag} onToggleTagPin={onToggleTagPin} />
        ) : null}
      </div>
      {allTagsWithPinned.length > tagsToShow.length ? (
        <Caption>
          <ButtonLink
            onClick={() => {
              setShowRunTags(true);
            }}
            color={Colors.textLight()}
            style={{margin: '-4px', padding: '4px'}}
          >
            View all tags ({allTagsWithPinned.length})
          </ButtonLink>
        </Caption>
      ) : null}

      {isHovered && allTagsWithPinned.length ? (
        <ShortcutHandler
          key="runtabletags"
          onShortcut={() => {
            setShowRunTags((showRunTags) => !showRunTags);
          }}
          shortcutLabel="t"
          shortcutFilter={(e) => e.code === 'KeyT'}
        >
          {null}
        </ShortcutHandler>
      ) : null}

      <Dialog
        isOpen={showRunTags}
        title="Tags"
        canOutsideClickClose
        canEscapeKeyClose
        onClose={() => {
          setShowRunTags(false);
        }}
      >
        <DialogBody>
          <RunTags tags={allTagsWithPinned} onAddTag={onAddTag} onToggleTagPin={onToggleTagPin} />
        </DialogBody>
        <DialogFooter topBorder>
          <CopyButton value={() => tagsAsYamlString(run.tags)}>Copy tags</CopyButton>
          <Button intent="primary" onClick={() => setShowRunTags(false)}>
            Close
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
};
