import React from "react";

import CategorySelectorMemo from "./CategorySelector";

import useSearchRequest, { Topics } from "../contexts/Search";

import {
  DialogContent,
  Dialog,
  DialogTitle,
  DialogActions,
  Button,
} from "@material-ui/core";

export function CategorySelectorDialogContent({
  onClose,
}: {
  onClose: () => void;
}) {
  const { filters, dispatch } = useSearchRequest();

  type ActionType = {
    mode: "add" | "del";
    value: string[];
  };
  const [categories, selectSubcategories] = React.useReducer(
    (s: Set<string>, action: ActionType) => {
      switch (action.mode) {
        case "add":
          return new Set([...Array.from(s), ...action.value]);
        case "del":
          const delSet = new Set(action.value);
          return new Set(Array.from(s).filter((x) => !delSet.has(x)));
      }
    },
    new Set<string>(filters.topics)
  );

  const addItem = React.useCallback(
    (values: string[]) => selectSubcategories({ mode: "add", value: values }),
    []
  );
  const deleteItem = React.useCallback(
    (values: string[]) => selectSubcategories({ mode: "del", value: values }),
    []
  );

  return (
    <>
      <DialogContent>
        <CategorySelectorMemo
          deleteItem={deleteItem}
          addItem={addItem}
          selectedSubcategoryCodes={categories}
          mode="research"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Annuler</Button>
        <Button
          onClick={() => {
            dispatch({
              type: "SET_CONSTRAINTS",
              constraintElement: {
                constraint: Topics,
                values: Array.from(categories),
              },
            });
            onClose();
          }}
        >
          Valider les {categories.size} catégories
        </Button>
      </DialogActions>
    </>
  );
}

export default function CategorySelectorDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  return (
    <Dialog open={open} onClose={onClose} fullWidth keepMounted={false}>
      <DialogTitle>Sélectionnez une catégorie</DialogTitle>
      <CategorySelectorDialogContent onClose={onClose} />
    </Dialog>
  );
}
