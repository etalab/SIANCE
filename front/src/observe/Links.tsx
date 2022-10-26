import { makeStyles } from "@material-ui/core";
import { Tree, LetterBlock, treeIsLeaf } from "../models/HydratedLetter";

export const useLinkStyles = makeStyles((theme) => ({
  demand: {},
  activatedDemand: {
    display: "inline-block",
    marginLeft: "1em",
    paddingLeft: "1em",
    marginTop: "1em",
    marginBottom: "1em",
    borderLeft: `1px solid ${theme.palette.success.main}`,
  },
  section: {
    margin: "1em",
    display: "block",
    whiteSpace: "pre-line",
  },
  activatedSection: {
    borderTop: `2px solid ${theme.palette.primary.main}`,
    borderBottom: `2px solid ${theme.palette.primary.main}`,
  },
  sentence: {},
  activatedSentence: {
    textDecoration: "underline",
    color: theme.palette.secondary.main,
  },
  activatedUncertainSentence: {
    color: theme.palette.primary.dark,
    textDecoration: "underline",
    fontWeight: 800

  },
  activatedLeaf: {
    background: theme.palette.info.main,
    color: theme.palette.info.contrastText,
  },
  leaf: {},
}));

export function buildClassNames(
  value: LetterBlock,
  activated: string,
  disabled: string,
  prefix: string
): string {
  const base = `${prefix}-${disabled}-${value.start}-${value.end} ${disabled}`;
  if (value.semantics.length > 0) {
    return `${base} ${activated}`;
  } else {
    return base;
  }
}

export function buildTreeKey(
  tree: Tree<LetterBlock, string>,
  disabled: string,
  prefix: string
): string {
  if (treeIsLeaf(tree)) {
    return tree.leaf;
  } else {
    return `${prefix}-${disabled}-${tree.value.start}-${tree.value.end}`;
  }
}
