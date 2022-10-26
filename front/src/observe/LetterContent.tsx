import React from "react";

import { match, parse } from "../lib/StringMatch";

import HydratedLetter, {
  Tree,
  LetterBlock,
  treeIsLeaf,
} from "../models/HydratedLetter";

import useSearchRequest from "../contexts/Search";

import { buildClassNames, buildTreeKey , useLinkStyles} from "./Links";

import { backTranslationCategory } from "./CategoryDisplay";

import {
  Snackbar,
  ButtonBase,
  Accordion,
  Typography,
  AccordionDetails,
  AccordionSummary,
  Tooltip,
} from "@material-ui/core";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";
import { makeStyles } from '@material-ui/core/styles';

const CONFIDENCE_THRESHOLD = 0.3;

/**
 * tree must be a tree of depth N
 * classes must be a list of depth >= N
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
  const l = level || 0;
  const linkStyles = useLinkStyles();

  let [acls, ...arest] = activatedClasses;
  let [dcls, ...drest] = disabledClasses;
  const { sentence: searchbarKeywords } = useSearchRequest();
  const [tooltipText, setTooltipText] = React.useState<string>("");

  if (treeIsLeaf(tree)) {
    const beginLine = tree.leaf.trim().split("\n\n")[0]
    const endLine = "\n" + tree.leaf.trim().split("\n\n").slice(1,).join("")
    if (
      10 < beginLine.length &&
      beginLine.length < 75 && // if the line is < 75, assume it is a title
      tree.leaf.toLowerCase().indexOf("action")  === -1 &&
      tree.leaf.toLowerCase().indexOf("information")  === -1 &&
      tree.leaf.toLowerCase().indexOf("observation")  === -1 &&
      tree.leaf.toLowerCase().indexOf("sans objet")  === -1 &&
      tree.leaf.toLowerCase().indexOf("demande")  === -1
    ) {
      return (
        <span id={buildTreeKey(tree, dcls, prefix)} className={dcls}>
          <span
            style={{
              color: "gray",
              border: 1,
              textDecoration:"underline",
              fontWeight: 600,
            }}
          >
            {beginLine}
          </span>
          <span
            style={{
              fontWeight: 400,
            }}
          >
            {endLine}
          </span>
        </span>
      )
    } else {
      const matches = match(tree.leaf, searchbarKeywords);
      const parts = parse(tree.leaf, matches);
      // highlight the keywords from the searchbar
      return (
        <span id={buildTreeKey(tree, dcls, prefix)} className={dcls}>
          {parts.map((part, i) => (
            <span
              key={i}
              style={{
                color: part?.highlight ? "orange" : undefined,
                fontWeight: part?.highlight ? 900 : 400,
              }}
            >
              {part.text}
            </span>
          ))}
        </span>
      );
    }

  } else {
    const cls = buildClassNames(tree.value, acls, dcls, prefix);
    switch (l) {
      case 0: // SECTIONS
        return (
          <span className={cls} id={buildTreeKey(tree, dcls, prefix)}>
            {tree.children.map((v) => (
              <TreeUnfold
                key={buildTreeKey(v, dcls, prefix)}
                tree={v}
                activatedClasses={arest}
                disabledClasses={drest}
                prefix={prefix}
                level={l + 1} // level = 1
              />
            ))}
          </span>
        );

      case 1: // DEMANDS
        if (tree.value.semantics.length > 0) {
          return (
            <ButtonBase
              component="span"
              className={cls}
              onClick={() => {
                navigator.clipboard.writeText(flattenTree(tree));
                setTooltipText(
                  `Demande ${tree.value.semantics[0].value} copiée dans le presse papier`
                );
                setTimeout(() => setTooltipText(""), 2500);
              }}
              id={buildTreeKey(tree, dcls, prefix)}
              title={"Cliquer ici pour copier la demande"}
            >
              {tree.children.map((v) => (
                <TreeUnfold
                  key={buildTreeKey(v, dcls, prefix)}
                  tree={v}
                  activatedClasses={arest}
                  disabledClasses={drest}
                  prefix={prefix}
                  level={l + 1} // level = 2
                />
              ))}
              {tooltipText && (
                <Snackbar
                  open={tooltipText !== ""}
                  anchorOrigin={{
                    vertical: "bottom",
                    horizontal: "center",
                  }}
                  message={tooltipText}
                  action={null}
                />
              )}
            </ButtonBase>
          );
        } else {
          return (
            <span className={cls} id={buildTreeKey(tree, dcls, prefix)}>
              {tree.children.map((v) => (
                <TreeUnfold
                  key={buildTreeKey(v, dcls, prefix)}
                  tree={v}
                  activatedClasses={arest}
                  disabledClasses={drest}
                  prefix={prefix}
                  level={l + 1} // level = 2
                />
              ))}
            </span>
          );
        }

      case 2: // PREDICTIONS
        // compute max of confidence score for the predictions in semacntics. Possibly undefined
        let confidences = tree.value.semantics.map(v=>v.confidence)
        let maximumConfidence = confidences.length > 0 ?confidences.reduce((a ,b) => a && b ? Math.max(a, b): undefined):undefined; 
        const isConfident = maximumConfidence && (maximumConfidence > CONFIDENCE_THRESHOLD)
        let title = tree.value.semantics.map((x) => x.value).join(", ") 
        title = title ? title + (isConfident ? "": " (prédiction incertaine)"): title
        return (
          <Tooltip title={title}>
            <span className={cls} id={buildTreeKey(tree, dcls, prefix)}>
              {
              tree.children.map((v) => {
                if (tree.value.semantics.length > 0) {
                  if (! isConfident) // return false if confidences are undefined
                  {
                    drest = [linkStyles.activatedUncertainSentence];
                  }

                }
                return (
                  <TreeUnfold
                    key={buildTreeKey(v, dcls, prefix)}
                    tree={v}
                    activatedClasses={arest}
                    disabledClasses={drest}
                    prefix={prefix}
                    level={l + 1} // level = 3
                  />
                )
              })
              }
            </span>
          </Tooltip>
        );

      default:
        // VOID
        return null;
    }
  }
}

const objectOfLetterRegex = /Objet/i;
function flattenTree(t: Tree<LetterBlock, string>): string {
  if (treeIsLeaf(t)) {
    return t.leaf;
  } else {
    return t.children.map(flattenTree).join("");
  }
}

function LetterIntroduction({
  introduction,
  disabledClasses,
}: {
  introduction: Tree<LetterBlock, string>;
  activatedClasses: string[];
  disabledClasses: string[];
  prefix: string;
}) {
  const trueIntroduction = React.useMemo(() => {
    const intro = flattenTree(introduction);
    const x = intro.match(objectOfLetterRegex);
    if (x?.index) {
      return intro.slice(x.index);
    } else {
      return intro;
    }
  }, [introduction]);

  const regexRefs = /(Réf.|Ref.|Refs.|Réfs.|Référence)[\s\S]*(Madame|Monsieur)/i;
  let m = trueIntroduction.match(regexRefs);
  const referentiel = m && m[0] ? m[0].split(/(Madame|Monsieur)/g)[0]:"";

  let start = trueIntroduction.indexOf(referentiel);
  let end = start + referentiel.length;
  const parts = parse(trueIntroduction, [[start, end]]);


  const useStyles = makeStyles(() => ({
    root: () => {
      return {
        color: "white",
        backgroundColor:  "teal"  // lighted teal
      };
    },
  }));
  
  return (
    <Accordion defaultExpanded={true}>
      <AccordionSummary expandIcon={<ExpandMoreIcon classes={useStyles()}/>} classes={useStyles()}>
        <Typography>Thème et références réglementaires</Typography>
      </AccordionSummary>
      <AccordionDetails>
      <span className={disabledClasses.join(" ")}>
        {parts.map((part, i) => (
          <span
            key={i}
            title="Vérifiez manuellement que ce référentiel est encore applicable"
            style={{
              color: part?.highlight ? "teal" : undefined,
              fontWeight: part?.highlight ? 600 : 400,
            }}
          >
            {part.text}
          </span>
        ))}
      </span>
      </AccordionDetails>
    </Accordion>
  );
}


function filterSelectedCategories(
  t: Tree<LetterBlock, string>,
  s: Set<string>,
  level: number = 0
): Tree<LetterBlock, string> {
  // the label sep char is defined in the python process builiding letter semantics blocks (letter_summary.py)

  if (treeIsLeaf(t)) {
    return t;
  } else {
    if (level === 2) {
      return {
        ...t,
        value: {
          start: t.value.start,
          end: t.value.end,
          semantics: t.value.semantics.filter((x) => s.has(backTranslationCategory(x.value)))
        },
      };
    } else {
      return {
        ...t,
        children: t.children.map((x) =>
          filterSelectedCategories(x, s, level + 1)
        ),
      };
    }
  }
}

function LetterContent({
  letter,
  activatedClasses,
  disabledClasses,
  selectedCategories,
  prefix,
}: {
  letter: HydratedLetter;
  activatedClasses: string[];
  disabledClasses: string[];
  prefix: string;
  selectedCategories: Set<string>;
}) {
  const [introduction, ...rest] = letter.content;

  const body = rest
    .map((x) => filterSelectedCategories(x, selectedCategories))
    .filter((x) => x !== undefined) as Tree<LetterBlock, string>[];

  return (
    <>
      <LetterIntroduction
        introduction={introduction}
        prefix={prefix}
        activatedClasses={activatedClasses}
        disabledClasses={disabledClasses}
      />
      {body.map((x) => (
        <TreeUnfold
          key={buildTreeKey(x, disabledClasses[0], prefix)}
          tree={x}
          prefix={prefix}
          activatedClasses={activatedClasses}
          disabledClasses={disabledClasses}
        />
      ))}
    </>
  );
}

export default LetterContent;
