import {
    TreeNode,
    TreeLeaf,
    LetterBlock,
    treeIsLeaf,
  } from "../models/HydratedLetter";

export function backTranslationCategory(category: string){
    const label_sep_char = " : ";
      if (category.indexOf(label_sep_char) > -1) {
          return category.split(label_sep_char)[1];
      } else {
        return category
      }
  }

 export function computeTopicsList(
    t: TreeNode<LetterBlock, string> | TreeLeaf<string> | undefined
  ): string[] {
    // the list of exact names of topics to displauy in the category selcetior 
    if (t === undefined) {
      return [];
    } else {
      if (treeIsLeaf(t)) {
        return [];
      } else {
        return [
          ...t.children.map((x) => computeTopicsList(x)),
          ...t.value.semantics
            .filter((v) => v.kind === "predictions")
            .map((v) => v.value),
        ].flat().map(backTranslationCategory);
      }
    }
  }