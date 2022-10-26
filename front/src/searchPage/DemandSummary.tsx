import React from "react";
import Typography from "@material-ui/core/Typography";

import { useHistory } from "react-router-dom";

import Button from "@material-ui/core/Button";

import CardContent from "@material-ui/core/CardContent";

import LibraryBooksIcon from "@material-ui/icons/LibraryBooks";
import LibraryAddCheckIcon from "@material-ui/icons/LibraryAddCheck";
import PageviewIcon from "@material-ui/icons/Pageview";

import { EDemand } from "../models/Demand";

import {
  Grid,
  makeStyles,
  Divider,
  CardHeader,
  Card,
  CardActions,
} from "@material-ui/core";

import { OpenPDF, OpenSIV2 } from "../components/LetterButtons";

import { useIsFresh } from "./contexts/SeenDocuments";

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
  openView: () => void;
  isCorrect: boolean;
  letter: EDemand;
};

function DemandSummary({
  openView,
  letter: doc,
  isCorrect,
}: LetterSummaryProps) {
  const styles = useStyles();
  const history = useHistory();
  const isFresh = useIsFresh(doc.id_letter);

  const domaines = [...doc.sectors, ...doc.domains, ...doc.natures].join(", ");
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
          <Button
            size="small"
            color="primary"
            href={`/find_letter?idLetter=${doc.id_letter}`}
            onClick={(e) => {
              e.preventDefault();
              history.push(`/find_letter?id_letter=${doc.id_letter}`);
            }}
          >
            <Typography variant="h5" color="primary" align="left">
              {isFresh ? (
                <LibraryBooksIcon fontSize="small" />
              ) : (
                <LibraryAddCheckIcon fontSize="small" />
              )}
              {doc.name}
            </Typography>
          </Button>
        }
        subheader={doc.demand_type}
      />
      <CardContent>
        <Typography
          style={{
            whiteSpace: "pre-line",
            maxHeight: "7.5rem",
            overflow: "hidden",
          }}
        >
          {doc.content.trim().slice(0, 250)}
          {doc.content.length > 250 ? "..." : ""}
        </Typography>
        <Divider />
        <Typography className={styles.summary}>
          Cette lettre, envoyée le{" "}
          <span className={styles.keyword}>
            {new Date(doc.date).toLocaleDateString("fr-FR", {
              weekday: "long",
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </span>{" "}
          par l'entité{" "}
          <span className={styles.keyword}>{doc.pilot_entity}</span> concerne{" "}
          <span className={styles.keyword}>
            {doc.interlocutor_name}
            {doc.site_name ? " " : ""}
            {doc.site_name}
            {doc.site_name ? " " : ", "}
          </span>
          {domaines !== "" ? (
            <>
              {" "}
              sur les domaines suivants:{" "}
              <span className={styles.keyword}>{domaines}</span>
            </>
          ) : null}
          . L'inspection avait pour thème{" "}
          <span className={styles.keyword}>{doc.theme}</span>.
        </Typography>
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
          <Grid item>
            <Button
              size="small"
              color="primary"
              title="Observer la lettre"
              onClick={openView}
            >
              <PageviewIcon />
            </Button>
          </Grid>
          <Grid item>
            <OpenPDF idLetter={doc.id_letter} name={doc.name} siv2={doc.siv2} />
          </Grid>
        </Grid>
      </CardActions>
    </Card>
  );
}

export default DemandSummary;
