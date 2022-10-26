// @ts-nocheck
import React from "react";

import ToggleButton from '@material-ui/lab/ToggleButton';
import ToggleButtonGroup from '@material-ui/lab/ToggleButtonGroup';
import { makeStyles } from "@material-ui/core/styles";
import { useDispatchModeLetters, elasticSorting } from "../searchPage/contexts/Modes";
import { ToggleModes } from "../searchPage/Types";
import useSearchRequest, { Sectors } from "../contexts/Search";
import {
  Grid,
} from "@material-ui/core";


const useStyles = makeStyles(() => ({
  root: () => {
    return {
      color: "gray",
    //  backgroundColor:  "#b2dfdb"  // lighted teal
    };
  },
}));


export function ToggleSectors(
  {mode}: {mode: ToggleModes["sectors"]}
){
  const { dispatch } = useSearchRequest();

  const handleChange = (event: React.MouseEvent<HTMLElement>, mode: ToggleModes["sectors"])=>{
    // on contrary to other toggles (below), this toggle directly dispatches its state 
    dispatch({
      type: "SET_CONSTRAINTS",
      constraintElement: {
        constraint: Sectors,
        values: mode,
      },
    })
  }

  return (
    <ToggleButtonGroup
      value={mode}
      onChange={handleChange}
      aria-label="sélection secteurs"
    >
      <ToggleButton value="REP" aria-label="REP" classes={useStyles()}>
        REP
      </ToggleButton>
      <ToggleButton value="LUDD" aria-label="LUDD" classes={useStyles()}>
        LUDD
      </ToggleButton>
      <ToggleButton value="NPX" aria-label="NPX" classes={useStyles()}>
        NPX
      </ToggleButton>
      <ToggleButton value="TSR" aria-label="TSR" classes={useStyles()}>
        TSR
      </ToggleButton>
      <ToggleButton value="ESP" aria-label="ESP" classes={useStyles()}>
        ESP
      </ToggleButton>
    </ToggleButtonGroup>
  )
}

export function ToggleSort({
  mode,
  setMode,
}:{
  mode: ToggleModes["sortOrder"];
  setMode: (mode: ToggleModes["sortOrder"])=>void 
}) {
  const { dispatch } = useSearchRequest();
  
  const handleChange = (event: React.MouseEvent<HTMLElement>, mode: ToggleModes["sortOrder"])=>{
    let sortDict = elasticSorting[elasticSorting.findIndex(
      (m) =>
        m.name === mode
    )].sort
    dispatch({
      type: "SET_SORTING",
      sorting: sortDict,
    })
    setMode(mode)
  }
  return (
    <ToggleButtonGroup
      value={mode}
      exclusive
      onChange={handleChange}
      aria-label="tri des résultats"
    >
      <ToggleButton value="SCORE" aria-label="score"  classes={useStyles()}>
        Pertinence ↓
      </ToggleButton>
      <ToggleButton value="DATE_DESC" aria-label="date décroissante"  classes={useStyles()}>
        Date ↓
      </ToggleButton>
      <ToggleButton value="DATE_ASC" aria-label="date croissante"  classes={useStyles()}>
        Date ↑
      </ToggleButton>
    </ToggleButtonGroup>
  );
}
  

export function ToggleLetters({
  mode,
  setMode
}:{
  mode: ToggleModes["letters"];
  setMode: (mode: ToggleModes["letters"])=>void
}) {
  const dispatchMode = useDispatchModeLetters() as React.Dispatch<ToggleModes["letters"]>;


  const handleChange = (event: React.MouseEvent<HTMLElement>, mode: ToggleModes["letters"])=>{
    setMode(mode);
    dispatchMode(mode)
  }
  return (
    <ToggleButtonGroup
      value={mode}
      exclusive
      onChange={handleChange}
      aria-label="sélection lettres/demandes"
    >
      <ToggleButton value={1} aria-label="lettres"  classes={useStyles()}>
        Lettres
      </ToggleButton>
      <ToggleButton value={2} aria-label="demandes"  classes={useStyles()}>
        Demandes
      </ToggleButton>
    </ToggleButtonGroup>
  );
}

export function ToggleGroup({
  modeLetters,
  setModeLetters,
  modeSort,
  setModeSort
}:{
  modeLetters: ToggleModes["letters"];
  setModeLetters: (mode: ToggleModes["letters"])=>void
  modeSort: ToggleModes["sortOrder"];
  setModeSort: (mode: ToggleModes["sortOrder"])=>void 
}){
  return (
    <Grid item container sm={12} justify="center" >
      <Grid item sm={7} align="right">
        <ToggleLetters mode={modeLetters} setMode={setModeLetters}/>
      </Grid>
      <Grid item sm={5} align="center">
        <ToggleSort mode={modeSort} setMode={setModeSort}/>
      </Grid>
    </Grid>
  )
} 