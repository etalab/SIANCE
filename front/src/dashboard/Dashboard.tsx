import React from "react";

import {
  Paper,
  Typography,
  Box,
  Card,
  Divider,
  CardHeader,
  CardContent,
  Grid,
  makeStyles,
} from "@material-ui/core";

import ImportExportIcon from "@material-ui/icons/ImportExport";
import FiltersPannel from "../components/Filters";

import { ToggleLetters } from "../components/ToggleButtons";
import { ModeLettersProvider, defaultModes } from "../searchPage/contexts/Modes";
import { ToggleModes } from "../searchPage/Types";


import { InspectDisplayProvider } from "../searchPage/contexts/Displays";

import useSearchRequest, {
 // constraintList,
 // ConstraintType,
} from "../contexts/Search";

import ExportButton from "../components/Export";

import ResponsiveDiv from "../graphs/ResponsiveDiv";
import {
  defaultDims,
  ResponsiveDateSelectionGraph,
} from "../graphs/histogram/DateHistogram";

import useStickyResult from "../hooks/Sticky";

import {useHistograms, useLettersCarto} from "../hooks/UseDashboardLetters";
import { VegaLite } from "react-vega";

import { FranceMapResponsive } from "../graphs/map/France";
//import useSuggestResponse from "../hooks/UseSuggestResponse";

const useStyles = makeStyles((theme) => ({
  modeSelection: {
    verticalAlign: "top",
  },
  filterPaper: {
    backgroundColor: theme.palette.background.default,
    padding: theme.spacing(2),
  },
}));

function DashboardPaper() {
  const style = useStyles();
  return (
    <Grid container spacing={2} direction="column">
      <Grid item xs={12}>
        <Paper className={style.filterPaper}>
          <Grid container alignItems="center">
            <Grid item>
              <ImportExportIcon />
            </Grid>
            <Grid item>
              <Typography variant="h6" gutterBottom>
                Exporter les résultats
              </Typography>
            </Grid>
          </Grid>
          <ExportButton mode={1} text="Exporter les lettres" />
          <ExportButton mode={2} text="Exporter les demandes" />
        </Paper>
      </Grid>
      <Grid item xs={12}>
        <Paper className={style.filterPaper}>
          <Typography variant="h6" gutterBottom>
            Filtres de recherche
          </Typography>
          <FiltersPannel />
        </Paper>
      </Grid>
    </Grid>
  );
}

/*
function Top2Items({ filter }: { filter: ConstraintType }) {
  const { data: suggestions } = useSuggestResponse("letters");
  const top2 =
    suggestions &&
    suggestions[filter.api]
      ?.slice(0, 2)
      .filter((suggestion) => suggestion.count && suggestion.count >= 5);
  return top2 && top2.length === 2 ? (
    <Grid item xs={12} md={6}>
      <Card>
        <CardHeader title={`Suivant le filtre ${filter.name}`} />
        <CardContent>
          <Grid container direction="column">
            {top2.map((suggestion) => (
              <Grid item xs={12}>
                <Typography variant="h4" color="secondary">
                  {suggestion.count} lettres
                </Typography>
                <Typography variant="h6" color="primary" gutterBottom>
                  {suggestion.value}
                </Typography>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    </Grid>
  ) : null;
}
*/

function DashboardGraphs({mode}:{mode:1|2|3}) {
  const request = useSearchRequest();
  const { daterange, dispatch } = request;
  const { data } = useLettersCarto(request);

  const histLetters = useStickyResult(data ? data.suggest_letters : undefined);
  const histDemands = useStickyResult(data ? data.suggest_demands : undefined);
  const geoData = useStickyResult(data ? data.dashboard : undefined);

  return (
    <>

      {mode !== 2 ? (
      <Grid item sm={12} md={12}>
        <Card variant="outlined">
          <CardHeader title="Évolution des lettres" />
          <CardContent>
            {histLetters && histLetters.date ? (
              <ResponsiveDiv>
                <ResponsiveDateSelectionGraph
                  unite="lettre"
                  data={histLetters.date.map(([key, doc_count]) => ({
                    key: new Date(key),
                    value: doc_count,
                  }))}
                  range={daterange}
                  setRange={(r) => {
                    dispatch({ type: "SET_DATE", date: r });
                  }}
                  graphDims={defaultDims}
                />
              </ResponsiveDiv>
            ) : null}
          </CardContent>
        </Card>
      </Grid>
      ): null}
      {mode === 2 ? (

      <Grid item sm={12} md={12}>
        <Card variant="outlined">
          <CardHeader title="Évolution des demandes" />
          <CardContent>
            {histDemands && histDemands.date ? (
              <ResponsiveDiv>
                <ResponsiveDateSelectionGraph
                  unite="demande"
                  data={histDemands.date.map(([key, doc_count]) => ({
                    key: new Date(key),
                    value: doc_count,
                  }))}
                  range={daterange}
                  setRange={(r) => {
                    dispatch({ type: "SET_DATE", date: r });
                  }}
                  graphDims={defaultDims}
                />
              </ResponsiveDiv>
            ) : null}
          </CardContent>
        </Card>
      </Grid>
      ): null}

      {
      /*constraintList
        .filter((constraintType) => constraintType.api !== "region")
        .map((constraintType) => (
          <Top2Items filter={constraintType} />
        ))
        */
        }
        
      <Grid item xs={12}>
        <Card variant="outlined">
          <CardHeader title="Répartition géographique" />
          <CardContent>
            <ResponsiveDiv>
              <FranceMapResponsive width={600} height={600} data={geoData} />
            </ResponsiveDiv>
          </CardContent>
        </Card>
      </Grid>
    </>
  );
}

function Histograms({mode}:{mode:1|2|3}) {
  const request = useSearchRequest();
  const response = useHistograms(request, mode);
  return (
    <>
    {
      response.data ?
        Object.keys(response.data).map((key) =>
        <Grid item sm={12} md={12}>
          <Card variant="outlined">
            <CardHeader title={"Top 10 principaux "+key.toLowerCase()} />
            <CardContent>
              <Grid item xs={8}>
                <VegaLite spec={response.data[key] as any} />
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        ):undefined
    }
    </>
  )
}

function Dashboard() {
  const [modeLetters, setModeLetters] = React.useState<ToggleModes["letters"]>(defaultModes["letters"]);

  return (
    <ModeLettersProvider>
      <InspectDisplayProvider>
        <Box m={3}>
          <Grid item container sm={12} justify="center" >
            <Grid item>
              <ToggleLetters mode={modeLetters} setMode={setModeLetters}/>
            </Grid>
          </Grid>
          <Divider/>
          <Grid container spacing={2} direction="row" alignItems="flex-start">
            <Grid item sm={6} md={5} lg={4}>
              <DashboardPaper />
            </Grid>
            <Grid
              item
              container
              sm={6}
              md={7}
              lg={8}
              spacing={2}
              direction="row"
              alignItems="stretch"
            >
              <DashboardGraphs mode={modeLetters}/>
              <Histograms mode={modeLetters}/>
            </Grid>

          </Grid>
        </Box>
      </InspectDisplayProvider>
    </ModeLettersProvider>
  );
}

export default Dashboard;
