import React from "react";

import {
  Grid,
  List,
  ListItem,
  ListItemIcon,
  Typography,
  Box,
  Button,
  Divider,
  CircularProgress,
  makeStyles,
} from "@material-ui/core";

import EmailIcon from "@material-ui/icons/Email";
import EventBusyIcon from "@material-ui/icons/EventBusy";
import ExitToAppIcon from "@material-ui/icons/ExitToApp";
import FilterListIcon from "@material-ui/icons/FilterList";
import ErrorIcon from "@material-ui/icons/Error";

import conf from "../config.json";

import { ELetter } from "../models/Letter";
import { EDemand } from "../models/Demand";

import useStickyResult from "../hooks/Sticky";
import LetterSummary from "./LetterSummary";
import DemandSummary from "./DemandSummary";

import useSearchRequest from "../contexts/Search";

import { useModeLetters } from "./contexts/Modes";
import { useInspectDispatchDisplay } from "./contexts/Displays";
import { useDispatchSeenLetters } from "./contexts/SeenDocuments";

import {
  computeInfiniteStatus,
  SearchResult,
  useCurrentInfiniteSearchResponse,
} from "../hooks/UseSearchResponse";

import { ErrorNotification } from "../Errors";

import { useLogout } from "../authentication/Utils";

const useStyles = makeStyles((theme) => ({
  pageDivider: {
    paddingTop: theme.spacing(2),
    paddingBottom: theme.spacing(-1),
  },
  centeredDividerSpan: {
    display: "inline-block",
    position: "relative",
    left: "50%",
    paddingLeft: theme.spacing(1),
    paddingRight: theme.spacing(1),
    backgroundColor: theme.palette.background.paper,
    transform: "translate(-50%,-50%)",
  },
}));

const PAGE_SIZE = conf.elasticsearch.page_size;

function NoResultText() {
  const dispatch = useInspectDispatchDisplay();
  const { daterange, dispatch: rdispatch } = useSearchRequest();
  return (
    <Grid container spacing={1}>
      <Grid item>
        <ErrorIcon color="secondary" fontSize="large" />
      </Grid>
      <Grid item>
        <Typography color="secondary" variant="h5">
          Nous ne trouvons aucun résultat pour cette recherche...
          {daterange[0]!==daterange[1]?
           " pour les années " + daterange[0]+"-"+daterange[1]
           : " pour l'année "+ daterange[0]
          }
        </Typography>
      </Grid>
      <Grid item sm={12}>
        <List>
          <ListItem button onClick={() => dispatch({ type: "SELECT_DATE" })}>
            <ListItemIcon>
              <EventBusyIcon />
            </ListItemIcon>
            Changer les dates
          </ListItem>
          <ListItem button onClick={() => rdispatch({ type: "RESET_FILTERS" })}>
            <ListItemIcon>
              <FilterListIcon />
            </ListItemIcon>
            Supprimer les filtres
          </ListItem>
          <ListItem
            button
            onClick={(e) => {
              e.preventDefault();
              window.open("http://si.asn.i2", "_blank");
            }}
          >
            <ListItemIcon>
              <ExitToAppIcon />
            </ListItemIcon>
            Ouvrir le SIv2
          </ListItem>
          <ListItem
            button
            onClick={(e) => {
              e.preventDefault();
              document.location.href = "mailto:contact-siance@asn.fr";
            }}
          >
            <ListItemIcon>
              <EmailIcon />
            </ListItemIcon>
            Contacter l'équipe
          </ListItem>
        </List>
      </Grid>
    </Grid>
  );
}

type ResultBlockSeparatorProps = {
  isEmpty: boolean;
  totalResult: number;
  index: number;
};

function ResultBlockSeparator({
  isEmpty,
  totalResult,
  index,
}: ResultBlockSeparatorProps) {
  return (
    <Grid
      container
      style={{ width: "100%" }}
      justify="space-between"
      alignItems="center"
    >
      <Grid item xs={3}>
        <Divider />
      </Grid>
      <Grid item xs={5} style={{ textAlign: "center" }}>
        <Typography component="span" variant="button">
          {isEmpty ? (
            ""
          ) : (
            <>
              Résultats de {index * PAGE_SIZE + 1} à{" "}
              {Math.min(totalResult, (index + 1) * PAGE_SIZE)} sur {totalResult===10000? ">"+totalResult: totalResult}{" "}
            </>
          )}
        </Typography>
      </Grid>
      <Grid item xs={index === 0 ? 2 : 4}>
        <Divider />
      </Grid>
      {
      /*index === 0 && (
        <Grid item xs={2} style={{ textAlign: "center" }}>
          <OrderSelection />
        </Grid>
      )
      */
      }
    </Grid>
  );
}

type ResultBlockEndProps = {
  isLoadingMore: boolean;
  isReachingEnd: boolean;
  setSize: (newSize: number) => void;
  size: number;
  totalResult: number;
  displayedResults: number;
};
function ResultBlockEnd({
  isLoadingMore,
  isReachingEnd,
  setSize,
  size,
  totalResult,
  displayedResults,
}: ResultBlockEndProps) {
  const styles = useStyles();
  return (
    <Box mb={-1} pt={2}>
      <Divider />
      <span className={styles.centeredDividerSpan}>
        <Button
          disabled={isLoadingMore || isReachingEnd}
          onClick={() => setSize(size + 1)}
        >
          {isLoadingMore ? (
            <CircularProgress />
          ) : isReachingEnd ? (
            "Fin des résultats"
          ) : (
            `Avancer dans les ${
              totalResult - displayedResults
            } résultats restants`
          )}
        </Button>
      </span>
    </Box>
  );
}

type ResultComponentProps<T> = {
  result: SearchResult<T>;
  isCorrect: boolean;
};

export function ResultListParametrized<T>({
  mode,
  Component,
}: {
  mode: number;
  Component: React.FunctionComponent<ResultComponentProps<T>>;
}) {
  const {
    data: undefinedSearchResult,
    error: searchError,
    isValidating,
    size,
    setSize,
  } = useCurrentInfiniteSearchResponse<T>(mode);
  const searchResult = useStickyResult(undefinedSearchResult);

  const logout = useLogout();

  const {
    totalResult,
    displayedResults,
    isRefreshing,
    isReachingEnd,
    isEmpty,
    isLoadingInitialData,
    isLoadingMore,
  } = computeInfiniteStatus<T>(
    searchError,
    isValidating,
    undefinedSearchResult,
    searchResult,
    size
  );

  const isCorrect = !isRefreshing && !isLoadingInitialData;

  React.useEffect(() => {
    if (!isValidating && searchError && true) {
      logout();
    }
  }, [isValidating, searchError, logout]);

  return (
    <>
      {searchResult &&
        searchResult.map((page, i) => (
          <React.Fragment key={i}>
            <Grid item xs={12} sm={12} key={i}>
              <ResultBlockSeparator
                index={i}
                isEmpty={isEmpty}
                totalResult={totalResult}
              />
            </Grid>
            {isEmpty ? (
              <Grid item xs={12} sm={12}>
                <NoResultText />
              </Grid>
            ) : null}
            {page.hits.map((document) => (
              <Grid item xs={12} lg={6} xl={4} key={document.doc_id}>
                <Component result={document} isCorrect={isCorrect} />
              </Grid>
            ))}
          </React.Fragment>
        ))}
      <Grid item xs={12} sm={12}>
        <ResultBlockEnd
          isLoadingMore={isLoadingMore}
          isReachingEnd={isReachingEnd}
          setSize={setSize}
          size={size}
          totalResult={totalResult}
          displayedResults={displayedResults}
        />
      </Grid>
      <ErrorNotification
        open={!isValidating && searchError && true}
        autoHideDuration={6000}
        message={`Une erreur est survenue : ${
          searchError?.message ||
          searchError?.status ||
          "Impossible de joindre le serveur. Êtes-vous bien connecté·e au VPN de l'ASN ? "
        }`}
      />
    </>
  );
}

export default function ResultList() {
  const { searchMode } = useModeLetters() as any;
  const dispatch = useInspectDispatchDisplay();
  const seenDispatch = useDispatchSeenLetters();

  switch (searchMode) {
    case 2: // demands
      return (
        <ResultListParametrized
          key="demands"
          mode={searchMode}
          Component={({ result, ...rest }: ResultComponentProps<EDemand>) => (
            <DemandSummary
              openView={() => {
                seenDispatch({
                  type: "add",
                  value: result._source.id_letter,
                });
                dispatch({
                  type: "VIEW_DEMAND",
                  selectedDemand: result,
                });
              }}
              letter={result._source}
              {...rest}
            />
          )}
        />
      );
    default:
      // letters
      return (
        <ResultListParametrized
          key="letters"
          mode={searchMode}
          Component={({ result, ...rest }: ResultComponentProps<ELetter>) => (
            <LetterSummary
              openView={() => {
                seenDispatch({
                  type: "add",
                  value: result._source.id_letter,
                });
                dispatch({
                  type: "VIEW_LETTER",
                  selectedLetter: result,
                });
              }}
              letter={result._source}
              docid={result.doc_id}
              highlighted={result.highlight}
              {...rest}
            />
          )}
        />
      );
  }
}
