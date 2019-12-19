import * as React from "react";
import styled from "styled-components/macro";
import { MenuItem, Menu, Popover, InputGroup } from "@blueprintjs/core";
import { PipelineExplorerSolidHandleFragment_solid } from "./types/PipelineExplorerSolidHandleFragment";

interface SolidQueryInputProps {
  solids: PipelineExplorerSolidHandleFragment_solid[];
  value: string;
  onChange: (value: string) => void;
}

interface ActiveSuggestionInfo {
  text: string;
  idx: number;
}

/** Generates placeholder text for the solid query box that includes a
 * practical example from the current DAG by finding the solid with the highest
 * number of immediate input or output connections and randomly highlighting
 * either the ++solid or solid++ or solid+* syntax.
 */
const placeholderTextForSolids = (
  solids: PipelineExplorerSolidHandleFragment_solid[]
) => {
  const seed = solids.length % 3;

  let placeholder = "Type a Solid Subset";
  if (solids.length === 0) return placeholder;

  const ranked = solids.map<{
    incount: number;
    outcount: number;
    name: string;
  }>(s => ({
    incount: s.inputs.reduce((sum, o) => sum + o.dependsOn.length, 0),
    outcount: s.outputs.reduce((sum, o) => sum + o.dependedBy.length, 0),
    name: s.name
  }));

  if (seed === 0) {
    const example = ranked.sort((a, b) => b.outcount - a.outcount)[0];
    placeholder = `${placeholder} (ex: ${example!.name}+*)`;
  } else if (seed === 1) {
    const example = ranked.sort((a, b) => b.outcount - a.outcount)[0];
    placeholder = `${placeholder} (ex: ${example!.name}+)`;
  } else if (seed === 2) {
    const example = ranked.sort((a, b) => b.incount - a.incount)[0];
    placeholder = `${placeholder} (ex: ++${example!.name})`;
  }
  return placeholder;
};

export const SolidQueryInput: React.FunctionComponent<SolidQueryInputProps> = props => {
  const [active, setActive] = React.useState<ActiveSuggestionInfo | null>(null);
  const [focused, setFocused] = React.useState<boolean>(false);

  const lastClause = /(\*?\+*)([\w\d_-]+)(\+*\*?)$/.exec(props.value);
  let menu: JSX.Element | undefined = undefined;

  const [, prefix, lastSolidName, suffix] = lastClause || [];
  const suggestions =
    lastSolidName && !suffix
      ? props.solids
          .map(s => s.name)
          .filter(n => n.startsWith(lastSolidName) && n !== lastSolidName)
      : [];

  const onConfirmSuggestion = (suggestion: string) => {
    const preceding = lastClause ? props.value.substr(0, lastClause.index) : "";
    props.onChange(preceding + prefix + suggestion + suffix);
  };

  if (suggestions.length && focused) {
    menu = (
      <StyledMenu>
        {suggestions.slice(0, 15).map(suggestion => (
          <StyledMenuItem
            key={suggestion}
            text={suggestion}
            active={active ? active.text === suggestion : false}
            onMouseDown={(e: React.MouseEvent<any>) => {
              e.preventDefault();
              e.stopPropagation();
              onConfirmSuggestion(suggestion);
            }}
          />
        ))}
      </StyledMenu>
    );
  }

  React.useEffect(() => {
    if (!active && suggestions.length) {
      setActive({ text: suggestions[0], idx: 0 });
      return;
    }
    if (!active) {
      return;
    }
    // Relocate the currently active item in the latest suggestions list
    const pos = suggestions.findIndex(a => a === active.text);

    // The new index is the index of the active item, or whatever item
    // is now at it's location if it's gone, bounded to the array.
    let nextIdx = pos !== -1 ? pos : active.idx;
    nextIdx = Math.max(0, Math.min(suggestions.length - 1, nextIdx));
    const nextText = suggestions[nextIdx];

    if (nextIdx !== active.idx || nextText !== active.text) {
      setActive({ text: nextText, idx: nextIdx });
    }
  }, [active, suggestions]);

  const onKeyDown = (e: React.KeyboardEvent<any>) => {
    if (e.key === "Enter" || e.key === "Return" || e.key === "Tab") {
      if (active && active.text) {
        onConfirmSuggestion(active.text);
        e.preventDefault();
        e.stopPropagation();
      }
    }

    // The up/down arrow keys shift selection in the dropdown.
    // Note: The first down arrow press activates the first item.
    const shift = { ArrowDown: 1, ArrowUp: -1 }[e.key];
    if (shift && suggestions.length > 0) {
      e.preventDefault();
      let idx = (active ? active.idx : -1) + shift;
      idx = Math.max(0, Math.min(idx, suggestions.length - 1));
      setActive({ text: suggestions[idx], idx });
    }
  };

  return (
    <SolidQueryInputContainer>
      <Popover
        minimal={true}
        isOpen={menu !== undefined}
        position={"bottom"}
        content={menu}
      >
        <SolidQueryInputField
          type="text"
          value={props.value}
          placeholder={placeholderTextForSolids(props.solids)}
          leftIcon={"send-to-graph"}
          onChange={(e: React.ChangeEvent<any>) =>
            props.onChange(e.target.value)
          }
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onKeyDown={onKeyDown}
        />
      </Popover>
    </SolidQueryInputContainer>
  );
};

const SolidQueryInputContainer = styled.div`
  z-index: 2;
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
`;

const SolidQueryInputField = styled(InputGroup)`
  font-size: 14px;
  width: 30vw;
`;

const StyledMenu = styled(Menu)`
  width: 30vw;
`;

const StyledMenuItem = styled(MenuItem)`
  font-size: 13px;
  line-height: 15px;
`;
