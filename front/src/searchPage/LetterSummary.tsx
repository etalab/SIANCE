import React from "react";
import Typography from "@material-ui/core/Typography";

import Button from "@material-ui/core/Button";

import CardContent from "@material-ui/core/CardContent";

import PageviewIcon from "@material-ui/icons/Pageview";

import Grid from "@material-ui/core/Grid";

import useSearchRequest from "../contexts/Search";
import { useIsFresh } from "./contexts/SeenDocuments";

import { ELetter } from "../models/Letter";

import { makeStyles, CardHeader, Card, CardActions } from "@material-ui/core";

import { OpenPDF, OpenSIV2, OpenObserve } from "../components/LetterButtons";

import LetterSummaryContent from "./LetterSummaryContents";

const useStyles = makeStyles((theme) => ({
  root: {
    ":visited.parent(&)": {
      filter: "grayscale(10%)",
    },
    height: "100%",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
  },
  summary: {
    color: theme.palette.text.secondary,
  },
  keyword: {
    color: theme.palette.text.primary,
  },
}));

type LetterSummaryProps = {
  openView?: () => void;
  isCorrect: boolean;
  letter: ELetter;
  highlighted: string[];
  docid: number;
};

function LetterSummary({
  openView,
  letter: doc,
  isCorrect,
}: LetterSummaryProps) {
  const isFresh = useIsFresh(doc.id_letter);
  const styles = useStyles();

  const { filters } = useSearchRequest();

  const actions = (doc.demands_a === 0) || (doc.demands_a === 1) ? "demande A" : "demandes A";
  const informations = (doc.demands_b === 0) || (doc.demands_b === 1) ? "demande B" : "demandes B";

  const domains = [...doc.sectors, ...doc.domains, ...doc.natures].join(", ");
  return (
    <Card
      className={styles.root}
      variant="outlined"
      style={{
        filter: !isCorrect
          ? "blur(2px) grayscale(100%)"
          : !isFresh
          ? "grayscale(100%)"
          : "none",
      }}
    >
      <CardHeader
        title={
          <Grid container>
            <Grid item xs={12} sm={6}>
              <OpenObserve idLetter={doc.id_letter} name={doc.name}>
                <Typography variant="h5" color="primary" align="left">
                  {doc.name}
                </Typography>
              </OpenObserve>
            </Grid>
            <Grid item xs={12} sm={6} style={{ textAlign: "right" }}>
              <Typography
                color="secondary"
                align="right"
                title="Demandes d'Action Correctives & Demandes d'Informations Complémentaires"
              >
                {doc.demands_a} {actions} <br /> {doc.demands_b} {informations}
              </Typography>
            </Grid>
          </Grid>
        }
      />
      <CardContent>
        <LetterSummaryContent
          letter={doc}
          filters={filters}
          summaryClass={styles.summary}
          keywordClass={styles.keyword}
          domains={domains}
        />
      </CardContent>
      <CardActions style={{ marginTop: "auto" }}>
        <Grid container justify="space-around">
          <Grid item>
            <OpenSIV2
              idLetter={doc.id_letter}
              name={doc.name}
              siv2={doc.siv2}
            />
          </Grid>
          {openView !== undefined && (
            <Grid item>
              <Button
                size="small"
                color="primary"
                title="Observer la lettre"
                onClick={openView}
                startIcon={<PageviewIcon />}
              >
                Résumé
              </Button>
            </Grid>
          )}
          <Grid item>
            <OpenPDF idLetter={doc.id_letter} name={doc.name} siv2={doc.siv2} />
          </Grid>
        </Grid>
      </CardActions>
    </Card>
  );
}

export default LetterSummary;
