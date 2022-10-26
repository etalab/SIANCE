import React from "react";

import {
  Button,
  Dialog,
  DialogContent,
  DialogActions,
  DialogTitle,
} from "@material-ui/core";

import { ConstraintType } from "../contexts/Search";

import AddFiltersToContext from "./FilterAutocomplete";

type FieldSelectionDialogProps = {
  constraint: ConstraintType;
  open: boolean;
  onClose: () => void;
};

export default function FieldSelectionDialog({
  constraint,
  open,
  onClose,
}: FieldSelectionDialogProps) {
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>
        Contraindre manuellement la valeur de « {constraint.name} »
      </DialogTitle>
      <DialogContent>
        <AddFiltersToContext filtersForAutocomplete={[constraint]} validateAction={onClose} />
      </DialogContent>
      <DialogActions>
        <Button variant="contained" onClick={onClose}>
          Annuler
        </Button>
      </DialogActions>
    </Dialog>
  );
}
