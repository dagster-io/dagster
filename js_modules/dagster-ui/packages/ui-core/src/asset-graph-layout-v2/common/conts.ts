/** The tension for the catmullrom curve. */
export const CATMULLROM_CURVE_TENSION = 0.1;

/** Cache for label width indexed by label. */

/** Whether the current browser is Mac. */
export const IS_MAC = typeof navigator !== 'undefined' && /Macintosh/.test(navigator.userAgent);

/** The maximum number of children nodes under a group node. */
export const DEFAULT_GROUP_NODE_CHILDREN_COUNT_THRESHOLD = 1000;

/** Y factor for elements rendered in webgl. */
export const WEBGL_ELEMENT_Y_FACTOR = 0.001;

/** Number of segments on a curve. */
export const WEBGL_CURVE_SEGMENTS = 25;

/** The key to expose test related objects. */
export const GLOBAL_KEY = 'me_test';

export const LAYOUT_MARGIN_X = 20;
