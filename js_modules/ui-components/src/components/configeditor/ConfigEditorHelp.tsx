import {memo} from 'react';

import {ConfigTypeSchema, TypeData} from '../ConfigTypeSchema';
import {ConfigEditorHelpContext} from './types/ConfigEditorHelpContext';
import {isHelpContextEqual} from '../configeditor/isHelpContextEqual';
import styles from './css/ConfigEditorHelp.module.css';

interface ConfigEditorHelpProps {
  context: ConfigEditorHelpContext | null;
  allInnerTypes: TypeData[];
}

export const ConfigEditorHelp = memo(
  ({context, allInnerTypes}: ConfigEditorHelpProps) => {
    if (!context) {
      return <div className={styles.container} />;
    }
    return (
      <div className={styles.container}>
        <div className={styles.configScrollWrap}>
          <ConfigTypeSchema type={context.type} typesInScope={allInnerTypes} maxDepth={2} />
        </div>
        <div className={styles.autocompletionsNote}>
          Use Ctrl+Space to show auto-completions inline.
        </div>
      </div>
    );
  },
  (prev, next) => isHelpContextEqual(prev.context, next.context),
);
