import React from "react";

import {
  Paper,
  Grid,
  IconButton,
  Typography,
  makeStyles,
  Box,
} from "@material-ui/core";
import { Datum } from "../graphs/histogram/Types";

import DateRangeIcon from "@material-ui/icons/DateRange";

//import FilterListIcon from "@material-ui/icons/FilterList";

import useStickyResult from "../hooks/Sticky";

import useSuggestResponse from "../hooks/UseSuggestResponse";

import {
  ResponsiveDateSelectionGraph,
  defaultDims,
} from "../graphs/histogram/DateHistogram";

import ResponsiveDiv from "../graphs/ResponsiveDiv";

import ParasDialog, { SelectedDemandDialog } from "./InspectDialog";
import { ControlsDialog } from "./Controls";
import ResultList from "./ResultList";


import { ToggleGroup } from "../components/ToggleButtons";
import useSearchRequest from "../contexts/Search";
import { ModeLettersProvider, useModeLetters, defaultModes } from "./contexts/Modes";
import { ToggleModes } from "./Types";

import FiltersPannel from "../components/Filters";
import useInspectDisplay, {
  useInspectDispatchDisplay,
  InspectDisplayProvider,
} from "./contexts/Displays";

import InspectSpeedDial from "./SpeedDial";

const useStyles = makeStyles((theme) => ({
  modeSelection: {
    verticalAlign: "sub",
  },
  filterPaper: {
    backgroundColor: theme.palette.background.default,
    padding: theme.spacing(2),
  },
  descriptionPaper: {
    backgroundColor: theme.palette.background.default,
    marginTop: theme.spacing(1),
    padding: theme.spacing(2),
    width: "100%",
  },
  floatingAction: {
    position: "absolute",
    bottom: theme.spacing(2),
    right: theme.spacing(4),
  },
}));

function SelectedDialogs() {
  const { selectedLetter, selectedDemand } = useInspectDisplay();
  return (
    <>
      <SelectedDemandDialog key={selectedDemand?.doc_id} />
      <ParasDialog key={selectedLetter?.doc_id} />
    </>
  );
}

export function InspectMiniDateSelector() {
  const { daterange: currentRange, dispatch: dispatchSearch } =
    useSearchRequest();
  const dispatchDisplay = useInspectDispatchDisplay();

  const { letters } = useModeLetters() as any;

  const { data: undefinedHistogramResult } = useSuggestResponse(
    letters === 2 ? "demands" : "letters"
  );

  const histogramResult = useStickyResult(undefinedHistogramResult);
  const today = new Date().toISOString();
  const newMillenial = new Date(2000,1,1).toISOString();
  const isValidDate =  (date: string | Date) => (today >= new Date(date).toISOString()) && (newMillenial <= new Date(date).toISOString())
  return (
    <>
      <Grid container alignItems="center">
        <Grid item>
          <IconButton
            onClick={() =>
              dispatchDisplay({
                type: "SELECT_DATE",
              })
            }
          >
            <DateRangeIcon />
          </IconButton>
        </Grid>
        <Grid item>
          <Typography variant="h6">Temporalité des résultats</Typography>
        </Grid>
      </Grid>

      {histogramResult ? (
        <ResponsiveDiv>
          <ResponsiveDateSelectionGraph
            unite={letters === 2 ? "demande" : "lettre"}
            data={histogramResult.date.map(([key, doc_count]) => 
              isValidDate(key) ?
              ({
                key: new Date(key),
                value: doc_count,
              }): undefined
            ).filter(Boolean) as Datum[]}
            range={currentRange}
            setRange={(r) => dispatchSearch({ type: "SET_DATE", date: r })}
            graphDims={{
              ...defaultDims,
              height: 100,
              margin: {
                top: 0,
                bottom: 0,
                left: 0,
                right: 0,
              },
            }}
            simple={true}
          />
        </ResponsiveDiv>
      ) : null}
    </>
  );
}

function SearchPaper() {
  const style = useStyles();
  return (
    <Paper className={style.filterPaper}>
      <Grid container spacing={2} justify="space-between">
        <Grid item sm={6} md={12}>
          <InspectMiniDateSelector />
        </Grid>
        <Grid item sm={6} md={12}>
          <FiltersPannel />
        </Grid>
      </Grid>
    </Paper>
  );
}

function SearchContent() {
  const [modeLetters, setModeLetters] = React.useState<ToggleModes["letters"]>(defaultModes["letters"]);
  const [modeSort, setModeSort] = React.useState<ToggleModes["sortOrder"]>(defaultModes["sortOrder"]);
  return (
    <>
      <Box m={3}>
        
        <Grid item container sm={12} justify="center" >
          <ToggleGroup
            modeLetters={modeLetters}
            setModeLetters={setModeLetters}
            modeSort={modeSort}
            setModeSort={setModeSort}
          />
        </Grid>

        <Grid container spacing={2} direction="row" alignItems="flex-start">
          <Grid item sm={12} md={5} lg={4}>
            <SearchPaper />
          </Grid>
          <Grid
            item
            container
            sm={12}
            md={7}
            lg={8}
            spacing={2}
            direction="row"
            alignItems="stretch"
          >
            <ResultList />
          </Grid>
        </Grid>
      </Box>
      <InspectSpeedDial />
      <ControlsDialog />
      <SelectedDialogs />
    </>
  );
}

function SearchPage() {
  return (
    <ModeLettersProvider>
      <InspectDisplayProvider>
        <SearchContent />
      </InspectDisplayProvider>
    </ModeLettersProvider>
  );
}
export default SearchPage;
