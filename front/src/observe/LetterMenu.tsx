import React from "react";

// import config from "../config.json";

import HydratedLetter, {
  Tree,
  LetterBlock,
  treeIsLeaf,
  treeIsNode,
} from "../models/HydratedLetter";

import { buildTreeKey } from "./Links";
import { ListItem, List, ListItemText } from "@material-ui/core";

const isInterestingNode = (
  t: Tree<LetterBlock, string>,
  level: number = 0
): boolean => {
  return (
    treeIsNode(t) &&
    t.children.length > 0 &&
    t.value.semantics.length > 0 &&
    t.value.semantics.some((x) => x.kind === "demands" || x.kind === "sections")
  );
};

export const translate = (
  s: "demands" | "predictions" | "sections",
  v: string
): string => {
  switch (s) {
    case "sections":
      if (v === "0") {
        return "Synthèse";
      } else {
        return `Section ${String.fromCharCode(Number(v) + 64)}`;
      }
    case "demands":
      return `Demande ${v}`;
    case "predictions":
      return "Prédiction";
    default:
      return "Inconnu";
  }
};

/*
 * Il faut mettre en place un contexte de traduction
 */

function TreeUnfold({
  tree,
  disabledClasses,
  activatedClasses,
  prefix,
  level,
}: {
  tree: Tree<LetterBlock, string>;
  activatedClasses: string[];
  disabledClasses: string[];
  prefix: string;
  level?: number;
}) {
  const arest = activatedClasses.slice(1);
  const [dcls, ...drest] = disabledClasses;
  const l = level || 0;

  if (treeIsLeaf(tree)) {
    return null;
  } else {
    return (
      <>
        <ListItem
          dense
          button
          component="a"
          href={`#${buildTreeKey(tree, dcls, prefix)}`}
        >
          <ListItemText
            primary={`${tree.value.semantics
              .map((x) => translate(x.kind, x.value))
              .join(", ")}`}
          />
        </ListItem>
        <List disablePadding component="div" style={{ paddingLeft: "1em" }}>
          {tree.children
            .filter((x) => isInterestingNode(x, l + 1))
            .map((v) => (
              <TreeUnfold
                key={buildTreeKey(v, dcls, prefix)}
                tree={v}
                activatedClasses={arest}
                disabledClasses={drest}
                prefix={prefix}
                level={l + 1}
              />
            ))}
        </List>
      </>
    );
  }
}

function LetterMenu({
  letter,
  activatedClasses,
  disabledClasses,
  prefix,
}: {
  letter: HydratedLetter;
  activatedClasses: string[];
  disabledClasses: string[];
  prefix: string;
}) {
  return (
    <List>
      {letter.content.filter(isInterestingNode).map((x) => (
        <TreeUnfold
          key={buildTreeKey(x, disabledClasses[0], prefix)}
          tree={x}
          prefix={prefix}
          activatedClasses={activatedClasses}
          disabledClasses={disabledClasses}
        />
      ))}
    </List>
  );
}

export default LetterMenu;
