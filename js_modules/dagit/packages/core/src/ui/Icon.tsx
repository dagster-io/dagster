import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';

// Mostly Material Design icons - need another one? Download the SVG:
// https://github.com/marella/material-design-icons/tree/main/svg/outlined

export const Icons = {
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
  delete: require('./icon-svgs/delete.svg'),
  done: require('./icon-svgs/done.svg'),
  download_for_offline: require('./icon-svgs/download_for_offline.svg'),
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
  linear_scale: require('./icon-svgs/linear_scale.svg'),
  link: require('./icon-svgs/link.svg'),
  location_on: require('./icon-svgs/location_on.svg'),
  menu: require('./icon-svgs/menu.svg'),
  menu_book: require('./icon-svgs/menu_book.svg'),
  open_in_new: require('./icon-svgs/open_in_new.svg'),
  refresh: require('./icon-svgs/refresh.svg'),
  schema: require('./icon-svgs/schema.svg'),
  search: require('./icon-svgs/search.svg'),
  settings: require('./icon-svgs/settings.svg'),
  settings_backup_restore: require('./icon-svgs/settings_backup_restore.svg'),
  sort_by_alpha: require('./icon-svgs/sort_by_alpha.svg'),
  source: require('./icon-svgs/source.svg'),
  speed: require('./icon-svgs/speed.svg'),
  star: require('./icon-svgs/star.svg'),
  table_view: require('./icon-svgs/table_view.svg'),
  toggle_off: require('./icon-svgs/toggle_off.svg'),
  toggle_on: require('./icon-svgs/toggle_on.svg'),
  view_list: require('./icon-svgs/view_list.svg'),
  visibility: require('./icon-svgs/visibility.svg'),
  warning: require('./icon-svgs/warning.svg'),
  workspaces: require('./icon-svgs/workspaces.svg'),
  zoom_in: require('./icon-svgs/zoom_in.svg'),
  zoom_out: require('./icon-svgs/zoom_out.svg'),
} as const;

export type IconName = keyof typeof Icons;

export const IconNames = Object.keys(Icons) as IconName[];

interface Props {
  color?: string;
  name: IconName;
  size?: 16 | 20 | 24 | 48;
}

export const IconWIP = (props: Props) => {
  const {color = ColorsWIP.Dark, name, size = 16} = props;
  let img = Icons[name] || require('./icon-svgs/test.svg');
  if (typeof img === 'object' && 'default' in img) {
    // in Dagit but not in Storybook due to webpack config differences
    img = img.default;
  }
  return <IconWrapper $color={color} $size={size} $img={img} role="img" aria-label={name} />;
};

export const IconWrapper = styled.div<{$color: string; $size: number; $img: string}>`
  color: ${(p) => p.$color};
  width: ${(p) => p.$size}px;
  height: ${(p) => p.$size}px;
  flex-shrink: 0;
  flex-grow: 0;
  background: ${(p) => p.$color};
  mask-image: url('${(p) => p.$img}');
  mask-size: cover;
  object-fit: cover;
`;
