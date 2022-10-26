import React from "react";
import {
  Paper,
  Typography,
  Button,
  Grid,
  makeStyles,
} from "@material-ui/core";
// @ts-ignore
import ReactFileReader from "react-file-reader";
import useWatchQueries from "../hooks/UseWatchQueries";
import useSearchRequest, {SearchRequestT} from "../contexts/Search";
import { ModeLettersProvider } from "../searchPage/contexts/Modes";
import { InspectMiniDateSelector } from "../searchPage/SearchPage";
import { InspectDisplayProvider } from "../searchPage/contexts/Displays";
import FiltersPannel from "../components/Filters";
import ImportExportIcon from "@material-ui/icons/ImportExport";
import useDownloadToken from "../hooks/UseDownloadToken";
import WatchTable from "./WatchTable"
import conf from "../config.json";

const useStyles = makeStyles((theme) => ({
  filterPaper: {
    backgroundColor: theme.palette.background.default,
    padding: theme.spacing(2),
  },
}));

function Watch() {

    const searchRequest = useSearchRequest()

    const [request, setRequest] = React.useState<SearchRequestT<string>[]>([])
    const { data: temporaryDownloadToken } = useDownloadToken();

    const {data } = useWatchQueries(request);
    let results = data?.results;
    const summaries = data?.summary;

    const formatRawCSV = (text: string):SearchRequestT<string>[]  => {
      const sentenceColumn = "keyword"
      const sep = ";"
      const regex = /(\r\n|\n)/;
      const table = text.split(regex)
      const headers = table[0].split(sep)
      const columnNumber = headers.findIndex((h: string) => h.toLowerCase().indexOf(sentenceColumn) > -1);
      const requests = table.splice(1,).map((row: string) => {
        let query;
        try{
          if (row.split(sep).length === headers.length){
            query = {
              sentence: row.split(sep)[columnNumber],
              filters: searchRequest.filters,
              daterange: searchRequest.daterange,
              sorting: searchRequest.sorting
            }
          }
        } catch {
        }
        return query
      }).filter(Boolean);
      return requests as unknown as SearchRequestT<string>[]
    }

    const handleFiles = (files: any) => {
        var reader = new FileReader();
        reader.onload = function(e) {
            // Use reader.result
            // interact with API
            if (reader.result) {
                const text = reader.result as string;
                setRequest(formatRawCSV(text))
            }
        }
        reader.readAsText(files[0]);
    }
    const style = useStyles();

    const urlDownload = results && request ?`${conf.api.url}/watch/download?watch=${encodeURI(
      JSON.stringify({"queries": request})
    )}&token=${
      temporaryDownloadToken?.download_token
    }`
    :"";

    return (
      <ModeLettersProvider>
        <InspectDisplayProvider>
        <Grid container spacing={2} direction="row">
        <Grid item sm={5} md={5} lg={4}>
          <Grid container spacing={2} direction="column">
          <Grid item>
            <Paper className={style.filterPaper}>
              <Grid container alignItems="center">
                <Grid item>
                  <ImportExportIcon />
                </Grid>
                <Grid item>
                  <Typography variant="h6" gutterBottom>
                    Importer des recherches
                  </Typography>
                </Grid>
              </Grid>
              <Typography variant="body2" gutterBottom>
                    Cette fonctionnalité permet de lancer plusieurs recherches succesivement, à partir d'un fichier de mots-clefs.
                    Ce fichier doit être un CSV, avec au moins une colonne qui doit être intitulée "keyword".
                    Le contenu de cette colonne indique les mots-clefs à rechercher successivement. Les mots-clefs sont ensuite combinés avec les filtres paramétrables ci-dessous (si les filtres sont modifiés, il faut ajouter à nouveau le fichier CSV).
                    S'il y a plusieurs colonnes dans ce fichier CSV, elles doivent être séparées par un point-virgule.
              </Typography>
              <ReactFileReader handleFiles={handleFiles} fileTypes={'.csv'}>
                  <Button
                    className='btn'
                    aria-label="excel-search-button"
                    size="small"
                    color="primary"
                  >
                    Ajouter des recherches - fichier CSV avec ;
                  </Button>
              </ReactFileReader>
            </Paper>
          </Grid>
          <Grid item>
            <Paper className={style.filterPaper}>
              <InspectMiniDateSelector/>
              <FiltersPannel />
            </Paper>
          </Grid>
        </Grid>
        </Grid>
        {
          summaries && summaries.length > 0? 
          <Grid item sm={7} md={7} lg={8}>

            <Grid>
                <Button
                 href={urlDownload}
                 disabled={!temporaryDownloadToken}
                 >Exporter l'ensemble des résultats</Button>
            </Grid>
            <Grid>
              <Typography variant="h5" gutterBottom>
                Synthèse de la recherche
              </Typography>
              <p>
                Tableau récapitulatif des lettres pertinents pour les mots-clefs recherchés.
                Du fait de la méthodologie de calcul, le nombre de résultats doit être considéré comme un ordre de grandeur.
                L'export exhaustif des résultats de votre veille sera disponible dans une version ultérieure de SIANCE.
              </p>
              <WatchTable summaries={summaries}/>
            </Grid>

          </Grid>
            :undefined
          }

        </Grid>
        </InspectDisplayProvider>
      </ModeLettersProvider>
    );

}

export default Watch
