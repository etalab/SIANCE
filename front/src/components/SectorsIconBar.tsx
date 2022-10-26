import React from "react";

import { Link, Grid, makeStyles, Badge } from "@material-ui/core";

import { useLettersSuggestResponse } from "../hooks/UseSuggestResponse";
import useSearchRequest, { Sectors } from "../contexts/Search";

const sectors = ["REP", "LUDD", "NPX", "TSR", "ESP"];

const useStyles = makeStyles((theme) => ({
  selected: {
    color: theme.palette.primary.light,
    "&:hover": {
      cursor: "pointer",
    },
    textDecorationLine: 'underline',   
    fontWeight: 'bold'
  },
  impossible: {
    color: theme.palette.error.light,
  },
  possible: {
    color: theme.palette.info.light,
    "&:hover": {
      cursor: "pointer",
    },
    textDecorationLine: 'underline',    
  },
}));

function SectorIcon({
  count,
  selected,
  sector,
  activate,
  deactivate,
}: {
  count: number | undefined;
  selected: boolean;
  sector: string;
  activate: () => void;
  deactivate: () => void;
}) {
  const status: "possible" | "selected" | "impossible" = selected
    ? "selected"
    : count !== undefined && count > 0
    ? "possible"
    : "impossible";

  const style = useStyles();

  return (
    <Badge badgeContent={count} max={99} className={style[status]}>
      <Link
        component="span"
        variant="body1"
        onClick={() =>
          status === "selected"
            ? deactivate()
            : status === "possible"
            ? activate()
            : null
        }
        className={style[status]}
      >
        {sector}
      </Link>
    </Badge>
  );
}

function SectorsIconBar() {
  const { data: rawSuggest } = useLettersSuggestResponse();
  const { filters, dispatch } = useSearchRequest();
  const counts = new Map(
    rawSuggest?.sectors.map((k) => [k.value, k.count || 0]) || []
  );
  const selection = new Set(filters.sectors);

  return (
    <Grid container spacing={1} justify="space-between">
      {sectors.map((sector) => (
        <Grid item key={sector}>
          <SectorIcon
            activate={() =>
              dispatch({
                type: "ADD_CONSTRAINT",
                constraintElement: {
                  constraint: Sectors,
                  values: [sector],
                },
              })
            }
            deactivate={() =>
              dispatch({
                type: "DEL_CONSTRAINT",
                constraintElement: {
                  constraint: Sectors,
                  values: [sector],
                },
              })
            }
            sector={sector}
            count={counts.get(sector)}
            selected={selection.has(sector)}
          />
        </Grid>
      ))}
    </Grid>
  );
}

export default SectorsIconBar;
