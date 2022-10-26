/*
 * Simple recursive data structure
 * with type of nodes different from
 * the type of leaves
 */

export type BlockSemantics<V> = {
  id_semantics: number;
  kind: "demands" | "predictions" | "sections";
  value: V;
  confidence?: number
};

export type LetterBlock = {
  start: number;
  end: number;
  semantics: BlockSemantics<string>[];
};

export type TreeNode<T, U> = {
  children: Tree<T, U>[];
  value: T;
};

export type TreeLeaf<U> = {
  leaf: U;
};

export type Tree<T, U> = TreeNode<T, U> | TreeLeaf<U>;

export function treeIsLeaf<T, U>(t: Tree<T, U>): t is TreeLeaf<U> {
  return (t as TreeLeaf<U>).leaf !== undefined;
}

export function treeIsNode<T, U>(t: Tree<T, U>): t is TreeNode<T, U> {
  return (t as TreeNode<T, U>).children !== undefined;
}

type HydratedLetter = {
  id_letter: number;
  name: string;
  codep: string;
  content: Tree<LetterBlock, string>[];
  date: Date;
  nb_pages?: number;
  //interlocutor: LetterInterlocutor;
  metadata_si?: { doc_id: string };
  //sections: LetterSection[];
  //demands: LetterDemand[];
  //predictions: LetterPrediction[];
};
export default HydratedLetter;
