import React from "react";
import {
  Grid,
  TextField,
  makeStyles,
  Theme,
  Dialog,
  DialogContent,
  DialogActions,
  DialogTitle,
  CircularProgress,
  Button,
} from "@material-ui/core";

import DateSelectionGraph, {
  defaultDims,
} from "../graphs/histogram/DateHistogram";

import useStickyResult from "../hooks/Sticky";
import useSuggestResponse from "../hooks/UseSuggestResponse";

// Contexts
import { useModeLetters } from "./contexts/Modes";
import useInspectDisplay, {
  useInspectDispatchDisplay,
} from "./contexts/Displays";
import useSearchRequest from "../contexts/Search";

const useStyles = makeStyles((theme: Theme) => ({
  sentenceInputContainer: {
    display: "flex",
    flexDirection: "row",
    flexFlow: "row wrap",
    alignItems: "center",
  },
  sentenceInputYear: {
    paddingLeft: theme.spacing(1),
    paddingRight: theme.spacing(1),
    maxWidth: "4em",
  },
  sentenceInputDelta: {
    paddingLeft: theme.spacing(1),
    paddingRight: theme.spacing(1),
    maxWidth: "2em",
  },
}));

function ControlsDialogContent() {
  const styles = useStyles();
  const {
    daterange: currentRange,
    dispatch: dispatchSearch,
  } = useSearchRequest();
  const dispatch = useInspectDispatchDisplay();
  const { letters } = useModeLetters() as any;

  const { data: undefinedHistogramResult } = useSuggestResponse(
    letters === 2 ? "demands" : "letters"
  );
  const histogramResult = useStickyResult(undefinedHistogramResult);

  const [localRange, setLocalRange] = React.useState(currentRange);

  const [startDate, endDate] = localRange;
  const deltaDate = endDate - startDate + 1;

  const currYear = new Date().getFullYear();

  const annees = deltaDate === 1 ? "an" : "ans";

  const minYear: number | undefined =
    (histogramResult &&
      histogramResult.date &&
      histogramResult.date[0] &&
      new Date(histogramResult.date[0][0]).getFullYear()) ||
    undefined;

  function cancel() {
    dispatch({ type: "CANCEL_DATE" });
  }

  function save() {
    dispatch({ type: "SAVE_DATE" });
    dispatchSearch({ type: "SET_DATE", date: localRange });
  }

  function handleDeltaSubmit(e: React.ChangeEvent<HTMLInputElement>) {
    const newEnd = Math.min(+e.target.value + startDate - 1, currYear);
    const newStart = newEnd - +e.target.value + 1;
    setLocalRange([newStart, newEnd]);
  }

  return (
    <>
      <DialogContent>
        <Grid
          container
          justify="space-around"
          alignItems="stretch"
          style={{ marginBottom: "1em" }}
        >
          <Grid item xs={6} sm={3}>
            <Button
              style={{ height: "100%" }}
              onClick={() => setLocalRange([currYear - 2, currYear])}
            >
              Deux dernières années
            </Button>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Button
              style={{ height: "100%" }}
              disabled={!minYear}
              onClick={() => setLocalRange([minYear || 2010, currYear])}
            >
              Ne pas contraindre la date
            </Button>
          </Grid>
        </Grid>
        Je recherche des {letters === 2 ? "demandes" : "lettres"} entre{" "}
        <TextField
          id="range-start"
          className={styles.sentenceInputYear}
          color="primary"
          type="number"
          value={startDate}
          error={deltaDate <= 0}
          onChange={(p) => setLocalRange([+p.target.value, endDate])}
        />{" "}
        et{" "}
        <TextField
          id="range-end"
          className={styles.sentenceInputYear}
          type="number"
          color="primary"
          value={endDate}
          error={deltaDate <= 0}
          onChange={(p) => setLocalRange([startDate, +p.target.value])}
        />
        . C'est à dire à partir de {startDate} et sur une période de{" "}
        <TextField
          id="range-width"
          type="number"
          color="primary"
          className={styles.sentenceInputDelta}
          value={deltaDate}
          error={deltaDate <= 0}
          onChange={handleDeltaSubmit}
        />{" "}
        {annees}.
        {histogramResult && histogramResult.date ? (
          <DateSelectionGraph
            unite={letters === 2 ? "demande" : "lettre"}
            data={histogramResult.date.map(([key, doc_count]) => ({
              key: new Date(key),
              value: doc_count,
            }))}
            range={localRange}
            setRange={setLocalRange}
            graphDims={{ ...defaultDims, height: 160 }}
            simple={false}
          />
        ) : (
          <CircularProgress />
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={cancel} color="primary">
          Annuler
        </Button>
        <Button onClick={save} color="primary" autoFocus>
          Valider
        </Button>
      </DialogActions>
    </>
  );
}

export function ControlsDialog() {
  const { showDateControls } = useInspectDisplay();
  const dispatch = useInspectDispatchDisplay();

  function cancel() {
    dispatch({ type: "CANCEL_DATE" });
  }

  return (
    <Dialog onClose={cancel} open={showDateControls} fullWidth={true}>
      <DialogTitle>Je sélectionne ma période d’intérêt</DialogTitle>
      <ControlsDialogContent />
    </Dialog>
  );
}
