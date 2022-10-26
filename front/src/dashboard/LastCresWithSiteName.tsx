import React from "react";
import {
  Card,
  CardHeader,
  CardContent,
  CircularProgress,
  makeStyles,
  CardActions,
  Tooltip
} from "@material-ui/core";

import useSearchRequest from "../contexts/Search";
import useCRES from "../hooks/UseCRES";

import { ECRES } from "../models/CRES";
import { OpenSIV2 } from "../components/LetterButtons";
//import {CombinedCompletionResult as Option} from "../hooks/UseCombinedCompletions";


function CRESSummary({ cres }: { cres: ECRES }) {
  let inb_information = cres.inb_information.map(x=>{
    if (isNaN(parseInt(x, 10))){
      return x
    } else {
      return "n°"+x
    }
  }).join(", ")
  return (
    <Card>
      <CardHeader title={cres.name} subheader={cres.date.toString()} />
      <Tooltip title={cres.summary}>
        <CardContent>
        <strong>Natures</strong>{" : "+ cres.natures.join(", ")} <br />
          <strong>{inb_information ?"INB":""}</strong> {inb_information ?" : " + inb_information:""} <br />
          <strong>Entreprise</strong> {" : "+ cres.interlocutor_name}, {cres.site_name} <br />
          <strong>Synthèse</strong> {" : "+cres.summary.slice(0, 300)}
          {cres.summary.length > 300 && "..."}
        </CardContent>
        </Tooltip>
      <CardActions>
        <OpenSIV2 idLetter={1} name={cres.name} siv2={cres.siv2} />
      </CardActions>
    </Card>
  );
}

const useHorizontalScrollStyle = makeStyles((theme) => ({
  root: {
    display: "grid",
    gridAutoFlow: "column",
    [theme.breakpoints.only("xl")]: {
      gridAutoColumns: "30%",
    },
    [theme.breakpoints.only("lg")]: {
      gridAutoColumns: "50%",
    },
    [theme.breakpoints.only("md")]: {
      gridAutoColumns: "60%",
    },
    [theme.breakpoints.only("sm")]: {
      gridAutoColumns: "90%",
    },
    [theme.breakpoints.only("xs")]: {
      gridAutoColumns: "110%",
    },
    gridGap: theme.spacing(1),
    overflowX: "scroll",
    overflowY: "hidden",
    paddingBottom: theme.spacing(1),
  },
}));

function HorizontalScrollGrid({ children }: { children: React.ReactNode }) {
  const styles = useHorizontalScrollStyle();
  return <div className={styles.root}>{children}</div>;
}

const id_interlocutor_constraint: number[] = [];
function LastCresWithSiteName({
   title,
}: {
  title?: React.ReactNode,
}) {

  const { filters } = useSearchRequest();

  const { data } = useCRES(
    filters.site_name,
    id_interlocutor_constraint,
    filters.interlocutor_name
  );

  const basicTitle =
    data && data.length > 0
      ? "Derniers ES de cet interlocuteur"
      : "Veuillez choisir un établissement/interlocuteur";
  return (
    <Card variant="outlined">
      <CardHeader title={title || basicTitle} />
      <CardContent>
        <HorizontalScrollGrid>
          {data ? (
            data.map((cres) => <CRESSummary key={cres.id_cres} cres={cres} />)
          ) : (
            <CircularProgress />
          )}
        </HorizontalScrollGrid>
      </CardContent>
    </Card>
  );
}

export default LastCresWithSiteName;
