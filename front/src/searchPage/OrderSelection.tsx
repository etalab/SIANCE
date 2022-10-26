import React from "react";
import useSearchRequest from "../contexts/Search";

import { Select, MenuItem, makeStyles } from "@material-ui/core";

const useStyles = makeStyles(() => ({
  modeSelection: {
    verticalAlign: "sub",
    minWidth: "160px",
    display: "flex",
  },
}));

const modes: {
  name: string;
  sort: { key: "_score" | "date"; order: "desc" | "asc" };
}[] = [
  { name: "Pertinence ↓", sort: { key: "_score", order: "desc" } },
  { name: "Date ↑", sort: { key: "date", order: "asc" } },
  { name: "Date ↓", sort: { key: "date", order: "desc" } },
];

function InspectSelectOrder() {
  const styles = useStyles();
  const { dispatch, sorting } = useSearchRequest();
  return (
    <>
      <Select
        className={styles.modeSelection}
        labelId="select-search-mode"
        id="select-search-mode"
        value={modes.findIndex(
          (mode) =>
            mode.sort.key === sorting.key && mode.sort.order === sorting.order
        )}
        title="Sélectionner le mode de recherche"
        onChange={(e) =>
          dispatch({
            type: "SET_SORTING",
            sorting: modes[e.target.value as number].sort,
          })
        }
      >
        {modes.map((mode, index) => (
          <MenuItem key={mode.name} value={index}>
            {mode.name}
          </MenuItem>
        ))}
      </Select>
    </>
  );
}

export default InspectSelectOrder;
