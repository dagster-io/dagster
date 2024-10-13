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
import styled from 'styled-components';

import {DagsterTag, TagType} from './RunTag';
import {RunTags} from './RunTags';
import {getBackfillPath} from './RunsFeedUtils';
import {RunFilterToken} from './RunsFilterInput';
import {RunTableRunFragment} from './types/RunTableRunFragment.types';
import {useTagPinning} from './useTagPinning';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {PipelineTag} from '../graphql/types';

export const RunRowTags = ({
  run,
  onAddTag,
  isHovered,
  isJob,
}: {
  run: Pick<RunTableRunFragment, 'tags' | 'assetSelection' | 'mode'>;
  onAddTag?: (token: RunFilterToken) => void;
  isHovered: boolean;
  isJob: boolean;
}) => {
  const {isTagPinned, onToggleTagPin} = useTagPinning();
  const [showRunTags, setShowRunTags] = React.useState(false);

  const allTagsWithPinned = React.useMemo(() => {
    const allTags: Omit<PipelineTag, '__typename'>[] = [...run.tags];
    if ((isJob && run.mode !== 'default') || !isJob) {
      allTags.push({key: 'mode', value: run.mode});
    }
    return allTags.map((tag) => {
      return {...tag, pinned: isTagPinned(tag)};
    });
  }, [run, isJob, isTagPinned]);

  const tagsToShow = React.useMemo(() => {
    const targetBackfill = allTagsWithPinned.find((tag) => tag.key === DagsterTag.Backfill);
    const tagKeys: Set<string> = new Set([]);
    const tags: TagType[] = [];

    if (targetBackfill && targetBackfill.pinned) {
      const link = getBackfillPath(targetBackfill.value, !!run.assetSelection?.length);
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
      if (tag.pinned) {
        tags.push(tag);
      }
    });
    return tags;
  }, [allTagsWithPinned, run.assetSelection?.length]);

  return (
    <>
      <RunTagsWrapper>
        {tagsToShow.length ? (
          <RunTags tags={tagsToShow} onAddTag={onAddTag} onToggleTagPin={onToggleTagPin} />
        ) : null}
      </RunTagsWrapper>
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
          <Button
            intent="primary"
            onClick={() => {
              setShowRunTags(false);
            }}
          >
            Close
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
};

const RunTagsWrapper = styled.div`
  display: contents;
  > * {
    display: contents;
  }
`;
