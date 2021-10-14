import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';

// Mostly Material Design icons - need another one? Download the SVG:
// https://github.com/marella/material-design-icons/tree/main/svg/outlined

const Icons = {
  // Core icons
  asset: require('./icon-svgs/table_view.svg'),
  expectation: require('./icon-svgs/bp-automatic-updates.svg'),
  job: require('./icon-svgs/account_tree.svg'),
  op: require('./icon-svgs/bp-git-commit.svg'),
  op_selector: require('./icon-svgs/bp-send-to-graph.svg'),
  op_dynamic: require('./icon-svgs/bolt.svg'),
  partition_set: require('./icon-svgs/schedule.svg'),
  repo: require('./icon-svgs/source.svg'),
  resource: require('./icon-svgs/layers.svg'),
  run: require('./icon-svgs/history.svg'),
  sensors: require('./icon-svgs/sensors.svg'),
  schedule: require('./icon-svgs/schedule.svg'),
  workspace: require('./icon-svgs/source.svg'),

  // Other renamed icons
  copy_to_clipboard: require('./icon-svgs/assignment.svg'),
  copy_to_clipboard_done: require('./icon-svgs/assignment_turned_in.svg'),

  // Material icons
  add_circle: require('./icon-svgs/add_circle.svg'),
  account_circle: require('./icon-svgs/account_circle.svg'),
  account_tree: require('./icon-svgs/account_tree.svg'),
  alternate_email: require('./icon-svgs/alternate_email.svg'),
  arrow_back: require('./icon-svgs/arrow_back.svg'),
  arrow_downward: require('./icon-svgs/arrow_downward.svg'),
  arrow_drop_down: require('./icon-svgs/arrow_drop_down.svg'),
  arrow_forward: require('./icon-svgs/arrow_forward.svg'),
  arrow_upward: require('./icon-svgs/arrow_upward.svg'),
  assignment: require('./icon-svgs/assignment.svg'),
  assignment_turned_in: require('./icon-svgs/assignment_turned_in.svg'),
  attach_file: require('./icon-svgs/attach_file.svg'),
  bolt: require('./icon-svgs/bolt.svg'),
  cached: require('./icon-svgs/cached.svg'),
  cancel: require('./icon-svgs/cancel.svg'),
  check_circle: require('./icon-svgs/check_circle.svg'),
  chevron_right: require('./icon-svgs/chevron_right.svg'),
  chevron_left: require('./icon-svgs/chevron_left.svg'),
  close: require('./icon-svgs/close.svg'),
  content_copy: require('./icon-svgs/content_copy.svg'),
  delete: require('./icon-svgs/delete.svg'),
  done: require('./icon-svgs/done.svg'),
  download_for_offline: require('./icon-svgs/download_for_offline.svg'),
  dynamic_feed: require('./icon-svgs/dynamic_feed.svg'),
  drag_handle: require('./icon-svgs/drag_handle.svg'),
  edit: require('./icon-svgs/edit.svg'),
  error: require('./icon-svgs/error.svg'),
  expand_less: require('./icon-svgs/expand_less.svg'),
  expand_more: require('./icon-svgs/expand_more.svg'),
  filter_alt: require('./icon-svgs/filter_alt.svg'),
  folder: require('./icon-svgs/folder.svg'),
  folder_open: require('./icon-svgs/folder_open.svg'),
  info: require('./icon-svgs/info.svg'),
  history: require('./icon-svgs/history.svg'),
  layers: require('./icon-svgs/layers.svg'),
  line_style: require('./icon-svgs/line_style.svg'),
  linear_scale: require('./icon-svgs/linear_scale.svg'),
  link: require('./icon-svgs/link.svg'),
  list: require('./icon-svgs/list.svg'),
  local_offer: require('./icon-svgs/local_offer.svg'),
  location_on: require('./icon-svgs/location_on.svg'),
  lock: require('./icon-svgs/lock.svg'),
  logout: require('./icon-svgs/logout.svg'),
  menu: require('./icon-svgs/menu.svg'),
  menu_book: require('./icon-svgs/menu_book.svg'),
  more_horiz: require('./icon-svgs/more_horiz.svg'),
  open_in_new: require('./icon-svgs/open_in_new.svg'),
  people: require('./icon-svgs/people.svg'),
  refresh: require('./icon-svgs/refresh.svg'),
  schema: require('./icon-svgs/schema.svg'),
  search: require('./icon-svgs/search.svg'),
  settings: require('./icon-svgs/settings.svg'),
  settings_backup_restore: require('./icon-svgs/settings_backup_restore.svg'),
  sort_by_alpha: require('./icon-svgs/sort_by_alpha.svg'),
  source: require('./icon-svgs/source.svg'),
  speed: require('./icon-svgs/speed.svg'),
  splitscreen: require('./icon-svgs/splitscreen.svg'),
  star: require('./icon-svgs/star.svg'),
  table_view: require('./icon-svgs/table_view.svg'),
  timer: require('./icon-svgs/timer.svg'),
  toggle_off: require('./icon-svgs/toggle_off.svg'),
  toggle_on: require('./icon-svgs/toggle_on.svg'),
  tune: require('./icon-svgs/tune.svg'),
  unfold_more: require('./icon-svgs/unfold_more.svg'),
  view_list: require('./icon-svgs/view_list.svg'),
  visibility: require('./icon-svgs/visibility.svg'),
  visibility_off: require('./icon-svgs/visibility_off.svg'),
  warning: require('./icon-svgs/warning.svg'),
  workspaces: require('./icon-svgs/workspaces.svg'),
  waterfall_chart: require('./icon-svgs/waterfall_chart.svg'),
  vertical_align_bottom: require('./icon-svgs/vertical_align_bottom.svg'),
  vertical_align_center: require('./icon-svgs/vertical_align_center.svg'),
  vertical_align_top: require('./icon-svgs/vertical_align_top.svg'),
  wysiwyg: require('./icon-svgs/wysiwyg.svg'),
  zoom_in: require('./icon-svgs/zoom_in.svg'),
  zoom_out: require('./icon-svgs/zoom_out.svg'),
} as const;

export type IconName = keyof typeof Icons;

const rotations: {[key in IconName]?: string} = {
  waterfall_chart: '-90deg',
};

export const IconNames = Object.keys(Icons) as IconName[];

interface Props {
  color?: string;
  name: IconName;
  size?: 16 | 20 | 24 | 48;
  style?: React.CSSProperties;
}

export const IconWIP = React.memo((props: Props) => {
  const {color = ColorsWIP.Dark, name, size = 16, style} = props;
  let img = Icons[name] || '';
  if (typeof img === 'object' && 'default' in img) {
    // in Dagit but not in Storybook due to webpack config differences
    img = img.default;
  }
  return (
    <IconWrapper
      role="img"
      $size={size}
      $img={img}
      $color={color}
      $rotation={rotations[name] || null}
      aria-label={name}
      style={style}
    />
  );
});

interface WrapperProps {
  $color: string;
  $size: number;
  $img: string;
  $rotation: string | null;
}

export const IconWrapper = styled.div<WrapperProps>`
  background: ${(p) => p.$color};
  width: ${(p) => p.$size}px;
  height: ${(p) => p.$size}px;
  flex-shrink: 0;
  flex-grow: 0;
  mask-image: url(${(p) => p.$img});
  mask-size: cover;
  object-fit: cover;
  transition: transform 150ms linear;

  ${({$rotation}) => ($rotation ? `transform: rotate(${$rotation});` : null)}
`;
