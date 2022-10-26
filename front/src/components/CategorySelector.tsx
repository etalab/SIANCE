import React from "react";

import { useDebounce } from "../api/Api";
import { HighlightedText } from "../lib/StringMatch";

import useOntology, {
  OntologyMetaProperties,
  OntologyTreeLeaf,
  OntologyTreeNode,
  OntologyTree,
} from "../hooks/UseOntology";

import {
  decorateLeafAll,
  decorateNodeAll,
  KeywordSearch,
  SelectedCategory,
  CountedCategories,
  foldOntology,
} from "./CategorySelectorUtils";

import { makeStyles, Theme, createStyles } from "@material-ui/core/styles";
import {
  List,
  ListItem,
  ListItemText,
  TextField,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  CircularProgress,
  Button,
  Grid,
  Collapse,
  Box,
  Divider,
  Checkbox,
} from "@material-ui/core";

import BookmarkIcon from "@material-ui/icons/Bookmark";
import BookmarksIcon from "@material-ui/icons/Bookmarks";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";
import ExpandLessIcon from "@material-ui/icons/ExpandLess";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: "100%",
      height: "20rem",
      overflowY: "scroll",
    },
    nested: {
      paddingLeft: theme.spacing(4),
    },
  })
);

function HighlightedTextDisplay({
  textDisplay,
  makeBold,
}: {
  textDisplay: HighlightedText[];
  makeBold?: boolean
}) {
  return (
    <React.Fragment key={textDisplay.map((t) => t.text).join()}>
      {textDisplay.map(({ text, highlight }, i) => (
        makeBold?
        <span key={i} style={{ fontWeight: highlight ? 1000 : 400 }}>
          <strong>{text}</strong>
        </span>
        :
        <span key={i} style={{ fontWeight: highlight ? 1000 : 400 }}>
          {text}
        </span>
      ))}
    </React.Fragment>
  );
}

function SubcategoryListItem<
  U extends {
    textDisplay: HighlightedText[];
    checked: boolean | undefined;
    count: number | undefined;
  }
>({
  item,
  deleteItem,
  addItem,
  shouldCount,
  makeBold
}: {
  item: OntologyTreeLeaf<U>;
  deleteItem: (subcatCodes: string[]) => void;
  addItem: (subcatCodes: string[]) => void;
  shouldCount: boolean;
  makeBold?: boolean
}) {
  const styles = useStyles();
  const deleteSelf = React.useCallback(() => deleteItem([item.subcategory]), [
    item.subcategory,
    deleteItem,
  ]);
  const addSelf = React.useCallback(() => addItem([item.subcategory]), [
    item.subcategory,
    addItem,
  ]);
  return (
    <ListItem
      button
      className={styles.nested}
      onClick={item.checked ? deleteSelf : addSelf}
    >
      <ListItemIcon>
        <Checkbox
          edge="start"
          checked={item.checked}
          tabIndex={-1}
          disableRipple
          inputProps={{
            "aria-labelledby": item.subcategory,
          }}
        />
      </ListItemIcon>
      <ListItemText
        primary={<HighlightedTextDisplay textDisplay={item.textDisplay} makeBold={makeBold} />}
        secondary={shouldCount && printResultNumbers(item)}
      />
    </ListItem>
  );
}

function printResultNumbers<
  T extends {
    count: number | undefined;
  },
  U extends {
    count: number | undefined;
  }
>(item: OntologyTreeNode<T, U> | OntologyTreeLeaf<U>): string {
  switch (item.count) {
    case undefined:
      return "Aucun résultat considéré comme fiable"; // "Aucune information sur cette catégorie";
    case 0:
      return "Aucun résultat";
    case 1:
      return "Au moins un résultat";
    default:
      return `Au moins ${item.count} résultats`;
  }
}

function CategoryListItem<
  T extends {
    textDisplay: HighlightedText[];
    shouldFold: boolean;
    checked: boolean | undefined;
    count: number | undefined;
    visible: boolean;
  },
  U extends {
    count: number | undefined;
    textDisplay: HighlightedText[];
    checked: boolean | undefined;
    visible: boolean;
  }
>({
  item,
  deleteItem,
  addItem,
  shouldCount,
  boldSubcategories
}: {
  item: OntologyTreeNode<T, U>;
  deleteItem: (subcatCodes: string[]) => void;
  addItem: (subcatCodes: string[]) => void;
  shouldCount: boolean;
  boldSubcategories?: string[]
}) {
  // explicit user control
  const [userExpanded, setExpanded] = React.useState<boolean | undefined>(
    undefined
  );
  const expanded = userExpanded === undefined ? !item.shouldFold : userExpanded;
  const toggleExpand = () => setExpanded(!expanded);

  const deleteSelf = React.useCallback(
    () => deleteItem(item.subcategories.map((subcat) => subcat.subcategory)),
    [item.subcategories, deleteItem]
  );

  const addSelf = React.useCallback(() => {
    const items = item.subcategories.map((subcat) => subcat.subcategory);
    addItem(items);
  }, [item.subcategories, addItem]);

  const intersect = function(array1: Array<string>, array2: Array<string>) {
    return array1.filter((value: string) => array2.includes(value)).length > 0
  }
  const makeBoldCategory = boldSubcategories ? intersect(
    item.subcategories.map(c=>c.subcategory),
    boldSubcategories
  ) : false;
  const hasNPX = item.subcategories.map(c=>c.is_npx).reduce((x: number,y: boolean)=>x+(+y), 0) > 0;
  const hasLUDD = item.subcategories.map(c=>c.is_ludd).reduce((x: number,y: boolean)=>x+(+y), 0) > 0;
  const hasREP = item.subcategories.map(c=>c.is_rep).reduce((x: number,y: boolean)=>x+(+y), 0) > 0;
  const sectors = [hasNPX?"NPX":undefined, hasREP?"REP":undefined, hasLUDD?"LUDD":undefined].filter(x=>x);
  let innerText = item.textDisplay[0]?.text;
  if (innerText && sectors.length > 0) {
    innerText += " ("+sectors.join(", ")+")"
  }
  const textDisplay = [{
    text: innerText,
    highlight: false
  }]
  return (
    <React.Fragment key={item.category}>
      <ListItem button onClick={toggleExpand}>
        <ListItemIcon>
          <IconButton edge="end" aria-label="collapse-open-close">
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </ListItemIcon>
        <ListItemText
          primary={<HighlightedTextDisplay textDisplay={textDisplay} makeBold={makeBoldCategory}/>}
          secondary={shouldCount && printResultNumbers(item)}
        />
        <ListItemSecondaryAction>
          <Checkbox
            onClick={item.checked ? deleteSelf : addSelf}
            edge="start"
            checked={item.checked !== false}
            indeterminate={item.checked === undefined}
            tabIndex={-1}
            disableRipple
            inputProps={{ "aria-labelledby": item.category }}
          />
        </ListItemSecondaryAction>
      </ListItem>
      <Collapse in={expanded} timeout="auto" unmountOnExit>
        {item.subcategories.map(
          (subcategory) =>
            subcategory.visible && (
              <SubcategoryListItem
                key={subcategory.id_label}
                item={subcategory}
                deleteItem={deleteItem}
                addItem={addItem}
                shouldCount={shouldCount}
                makeBold={boldSubcategories?boldSubcategories.includes(subcategory.subcategory):false}
              />
            )
        )}
      </Collapse>
    </React.Fragment>
  );
}

const MemoizedCategoryListItem = React.memo(
  CategoryListItem,
  (prevprops, nextprops) => {
    return (
      prevprops.item.visible === nextprops.item.visible &&
      prevprops.item.shouldFold === nextprops.item.shouldFold &&
      prevprops.item.checked === nextprops.item.checked &&
      prevprops.item.textDisplay.length === nextprops.item.textDisplay.length &&
      prevprops.item.subcategories
        .map((x) => `${x.id_label}${x.checked}${x.textDisplay.length}}`)
        .join("") ===
        nextprops.item.subcategories
          .map((x) => `${x.id_label}${x.checked}${x.textDisplay.length}}`)
          .join("")
    );
  }
);

function CategoryList<
  T extends {
    textDisplay: HighlightedText[];
    shouldFold: boolean;
    checked: boolean | undefined;
    count: number | undefined;
    visible: boolean;
  },
  U extends {
    textDisplay: HighlightedText[];
    checked: boolean | undefined;
    count: number | undefined;
    visible: boolean;
  }
>({
  tree,
  deleteItem,
  addItem,
  shouldCount,
  boldSubcategories
}: {
  tree: OntologyTree<T, U>;
  deleteItem: (subcatCodes: string[]) => void;
  addItem: (subcatCodes: string[]) => void;
  shouldCount: boolean;
  boldSubcategories?: string[]
}) {
  const styles = useStyles();
  if (boldSubcategories){
    return (
      <List className={styles.root}>
      {tree.map(
        (item) =>
          item.visible && (
            <CategoryListItem
              key={item.category}
              item={item}
              deleteItem={deleteItem}
              addItem={addItem}
              shouldCount={shouldCount}
              boldSubcategories={boldSubcategories}
            />
          )
      )}
    </List>
    )
  } else {
    return (
      <List className={styles.root}>
        {tree.map(
          (item) =>
            item.visible && (
              <MemoizedCategoryListItem
                key={item.category}
                item={item}
                deleteItem={deleteItem}
                addItem={addItem}
                shouldCount={shouldCount}
                boldSubcategories={boldSubcategories}
              />
            )
        )}
      </List>
    );
  }
}

const MemoizedCategoryListDisplay = React.memo(CategoryList);

function CategorySelector({
  deleteItem,
  addItem,
  restrictToCodes,
  selectedSubcategoryCodes,
  mode,
  subcategoriesCount,
  boldSubcategories
}: {
  subcategoriesCount?: Map<string, number>;
  restrictToCodes?: Set<string>;
  selectedSubcategoryCodes: Set<string>;
  mode?: keyof OntologyMetaProperties;
  deleteItem: (subcatCodes: string[]) => void;
  addItem: (subcatCodes: string[]) => void;
  boldSubcategories?: string[]
}) {
  // codes are "subcategories", namely bottom elements in hierarchichal menu
  const { data } = useOntology();

  const [keyword, setKeyword] = React.useState<string>("");
  const [viewMode, setViewMode] = React.useState<"all" | "selected">("all");
  const viewAll = () => setViewMode("all");
  const viewSelected = () => setViewMode("selected");
  const userKeyword = useDebounce(keyword, 500);

  const tree = React.useMemo(() => {
    const decorateLeaf = (leaf: OntologyTreeLeaf<{}>) =>
      decorateLeafAll<{}>(
        selectedSubcategoryCodes,
        userKeyword,
        subcategoriesCount || new Map<string, number>(),
        viewMode,
        mode,
        restrictToCodes,
        leaf
      );
    const decorateNode = (
      node: OntologyTreeNode<
        {},
        SelectedCategory &
          KeywordSearch &
          CountedCategories & { visible: boolean }
      >
    ) =>
      decorateNodeAll<
        {},
        SelectedCategory &
          KeywordSearch &
          CountedCategories & { visible: boolean }
      >(userKeyword, node);
    return data ? foldOntology(decorateLeaf, decorateNode, data) : undefined;
  }, [
    userKeyword,
    mode,
    viewMode,
    data,
    selectedSubcategoryCodes,
    restrictToCodes,
    subcategoriesCount,
  ]);

  return (
    <>
      <TextField
        id="standard-basic"
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        label="Catégorie ou sous-catégorie"
        fullWidth
      />
      {tree ? (
        <MemoizedCategoryListDisplay
          deleteItem={deleteItem}
          addItem={addItem}
          tree={tree}
          shouldCount={subcategoriesCount !== undefined}
          boldSubcategories={boldSubcategories}
        />
      ) : (
        <CircularProgress />
      )}
      <Box p={2}>
        <Divider />
      </Box>
      <Grid container justify="center" spacing={2}>
        <Grid item>
          <Button
            key="all"
            color="primary"
            variant={viewMode === "all" ? "contained" : "outlined"}
            disabled={viewMode === "all"}
            onClick={viewAll}
            title="Tout voir"
            startIcon={<BookmarksIcon />}
          >
            Tout
          </Button>
        </Grid>

        <Grid item>
          <Button
            key="selected"
            color="primary"
            variant={viewMode === "selected" ? "contained" : "outlined"}
            disabled={viewMode === "selected"}
            onClick={viewSelected}
            title="Voir la sélection"
            startIcon={<BookmarkIcon />}
          >
            Sélection
          </Button>
        </Grid>
      </Grid>
    </>
  );
}
const CategorySelectorMemo = React.memo(CategorySelector);
export default CategorySelectorMemo;
