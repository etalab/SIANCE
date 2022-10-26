import { match, parse, HighlightedText } from "../lib/StringMatch";

import {
  OntologyTree,
  OntologyTreeLeaf,
  OntologyTreeNode,
  OntologyMetaProperties,
} from "../hooks/UseOntology";

export function searchParts(s: string, t: string) {
  const matches = match(t, s);
  const parts = parse(t, matches);
  const itemMatches = s === "" || matches.length > 0;
  return [parts, itemMatches] as const;
}

/*
 * super reducer
 */
export function foldOntology<T, U, V, W>(
  f: (leaf: OntologyTreeLeaf<U>) => OntologyTreeLeaf<W>,
  g: (node: OntologyTreeNode<T, W>) => OntologyTreeNode<V, W>,
  t: OntologyTree<T, U>
): OntologyTree<V, W> {
  return t.map((node) =>
    g({ ...node, subcategories: node.subcategories.map(f) })
  );
}

export function filterLeavesAndRemoveOrphans<T, U>(
  f: (leaf: OntologyTreeLeaf<U>) => boolean,
  t: OntologyTree<T, U>
) {
  return foldOntology(
    (x) => x,
    (node) => ({ ...node, subcategories: node.subcategories.filter(f) }),
    t
  ).filter((node) => node.subcategories.length > 0);
}

/*
 * The decorators using the keyword search
 * of the user
 *
 * - it adds KeywordSearch values to leaves
 * - it adds KeywordSearchCategory values to nodes
 *
 */

export type KeywordSearch = {
  textDisplay: HighlightedText[];
  isMatching: boolean;
};

export type KeywordSearchCategory = KeywordSearch & {
  shouldFold: boolean;
};

export function decorateLeafUsingKeyword<U>(
  keyword: string,
  leaf: OntologyTreeLeaf<U>
): OntologyTreeLeaf<U & KeywordSearch> {
  const [parts, itemMatches] = searchParts(keyword, leaf.subcategory);
  return { ...leaf, textDisplay: parts, isMatching: itemMatches };
}

export function decorateNodeUsingKeyword<T, U>(
  keyword: string,
  node: OntologyTreeNode<T, U & KeywordSearch>
): OntologyTreeNode<T & KeywordSearchCategory, U & KeywordSearch> {
  const [parts, itemMatches] = searchParts(keyword, node.category);
  return {
    ...node,
    textDisplay: parts,
    isMatching: itemMatches,
    shouldFold:
      itemMatches || node.subcategories.every((leaf) => leaf.isMatching),
  };
}

/*
 * Utilizes the selection of categories as a flat Set<string>
 * to decorate the tree of categories
 * with SelectedCategory
 */
export type SelectedCategory = {
  checked: true | false | undefined;
};

export function decorateLeafChecked<U>(
  subcategoryCodes: Set<string>,
  leaf: OntologyTreeLeaf<U>
): OntologyTreeLeaf<U & SelectedCategory> {
  return { ...leaf, checked: subcategoryCodes.has(leaf.subcategory) };
}

export function decorateNodeChecked<T, U extends SelectedCategory>(
  node: OntologyTreeNode<T, U>
): OntologyTreeNode<T & SelectedCategory, U> {
  const every = node.subcategories.every((leaf) => leaf.checked);
  const some = node.subcategories.some((leaf) => leaf.checked);
  return {
    ...node,
    checked: every ? true : some ? undefined : false,
  };
}

/*
 * Decoration
 * with counts
 */
export type CountedCategories = {
  count: undefined | number;
};

export function decorateLeafCount<U>(
  subcategoriesCount: Map<string, number>,
  leaf: OntologyTreeLeaf<U>
): OntologyTreeLeaf<U & CountedCategories> {
  return {
    ...leaf,
    count: subcategoriesCount.get(leaf.subcategory),
  };
}

export function decorateNodeCount<U, V>(
  node: OntologyTreeNode<U, V & CountedCategories>
): OntologyTreeNode<U & CountedCategories, V & CountedCategories> {
  const sum = node.subcategories.reduce((a, b) => a + (b.count || 0), 0);
  const hasInfo = node.subcategories.some((x) => x.count !== undefined);
  return {
    ...node,
    count: hasInfo ? sum : undefined,
  };
}

/**
 *
 * Instead of filtering nodes we add a property
 * « visible ». invisible nodes are filtered
 * at rendering time.
 *
 */
export function decorateLeafVisible<U>(
  userKeyword: string,
  viewMode: "all" | "selected",
  mode: keyof OntologyMetaProperties | undefined,
  restrictToCodes: Set<string> | undefined,
  leaf: OntologyTreeLeaf<
    U & SelectedCategory & CountedCategories & KeywordSearch
  >
) {
  return {
    ...leaf,
    visible:
      ((userKeyword === "" || leaf.isMatching) &&
        (viewMode === "all" || leaf.checked) &&
        (mode === undefined || leaf[mode] === true) &&
       // (mode !=="research" || leaf.count !== undefined) &&
        (restrictToCodes === undefined ||
          restrictToCodes.has(leaf.subcategory))
      ) ||
      false,
  };
}
export function decorateNodeVisible<T, U>(
  node: OntologyTreeNode<
    T,
    U & { visible: boolean } & CountedCategories &
      SelectedCategory &
      KeywordSearch
  >
) {
  return {
    ...node,
    visible: node.subcategories.some((subcat) => subcat.visible),
  };
}

export function decorateLeafAll<U>(
  subcategoryCodes: Set<string>,
  keyword: string,
  subcategoriesCount: Map<string, number>,
  viewMode: "all" | "selected",
  mode: keyof OntologyMetaProperties | undefined,
  restrictToCodes: Set<string> | undefined,
  leaf: OntologyTreeLeaf<U>
): OntologyTreeLeaf<
  U &
    SelectedCategory &
    KeywordSearch &
    CountedCategories & { visible: boolean }
> {
  return decorateLeafVisible(
    keyword,
    viewMode,
    mode,
    restrictToCodes,
    decorateLeafCount(
      subcategoriesCount,
      decorateLeafChecked(
        subcategoryCodes,
        decorateLeafUsingKeyword(keyword, leaf)
      )
    )
  );
}

export function decorateNodeAll<T, U>(
  keyword: string,
  node: OntologyTreeNode<
    T,
    U &
      CountedCategories &
      SelectedCategory &
      KeywordSearch & { visible: boolean }
  >
): OntologyTreeNode<
  T &
    SelectedCategory &
    KeywordSearchCategory &
    CountedCategories & { visible: boolean },
  U &
    SelectedCategory &
    KeywordSearch &
    CountedCategories & { visible: boolean }
> {
  return decorateNodeCount(
    decorateNodeChecked(
      decorateNodeUsingKeyword(keyword, decorateNodeVisible(node))
    )
  );
}
