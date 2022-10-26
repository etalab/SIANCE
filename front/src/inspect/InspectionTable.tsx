import React from "react";
import { InterlocutorName, Theme as ThemeName } from "../contexts/Search";
import { useLastResultsMatching } from "../hooks/UseSearchResponse";
//import {CombinedCompletionResult as Option} from "../hooks/UseCombinedCompletions";

import useSearchRequest, { ConstraintType } from "../contexts/Search";

import {
  Table,
  Button,
  Snackbar,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@material-ui/core";
import FileCopyIcon from '@material-ui/icons/FileCopy';
import CheckIcon from "@material-ui/icons/Check";

import { withStyles, Theme, createStyles } from "@material-ui/core/styles";

const StyledTableCell = withStyles((theme: Theme) =>
  createStyles({
    head: {
      backgroundColor: theme.palette.primary.dark,
      color: theme.palette.common.white,
    },
    body: {
      fontSize: 14,
    },
  })
)(TableCell);

export default function InspectionTable({
  filter,
//  values
}: {
  filter: ConstraintType;
//  values: Option[]
}) {

  const { filters } = useSearchRequest();
  const values = filters[filter.api];
  const { data } = useLastResultsMatching(filter, values);
  
  const results = data && data.hits; // read top results
  const letters = results?.map((result) => result._source);

  // if the component is filtering inspections by interlocutor, display inspections of the same theme. And inversely
  // the component should be made more generic later
  let displayFilter = ["Entreprise", "Nom du site"].indexOf(filter.name) > -1 ? ThemeName : InterlocutorName;

  const tableHead = (
    <TableHead>
      <TableRow>
        <StyledTableCell align="left">Nom de l'inspection</StyledTableCell>
        <StyledTableCell align="left">Date</StyledTableCell>
        <StyledTableCell align="left">{displayFilter.name}</StyledTableCell>
        <StyledTableCell align="left">Demandes A</StyledTableCell>
        <StyledTableCell align="left">Demandes B</StyledTableCell>
        <StyledTableCell align="left">Dossier d'inspection</StyledTableCell>
      </TableRow>
    </TableHead>
  );

  //   <a href={"http://si.asn.i2/webtop/drl/objectId/" + letter.siv2}>
  const [copyTooltip, setCopyTooltip] = React.useState<boolean[]>([false, false, false, false]);

  let lettersRows = letters?.map((letter, k) => (
    <TableRow>
      <StyledTableCell align="left">
        {letter.id_letter ? (
          <a href={"/find_letter?id_letter=" + letter.id_letter}>
            {letter.name}
          </a>
        ) : (
          letter.name
        )}
      </StyledTableCell>
      <StyledTableCell align="left">{letter.date}</StyledTableCell>
      <StyledTableCell align="left">
        {letter[displayFilter.api as ("theme" | "interlocutor_name" | "site_name")]}
      </StyledTableCell>
      <StyledTableCell align="left">{letter.demands_a}</StyledTableCell>
      <StyledTableCell align="left">{letter.demands_b}</StyledTableCell>
      <StyledTableCell align="left">
        <Button
          size="small"
          color="primary"
          disabled={!letter.siv2}
          startIcon={copyTooltip[k] ? <CheckIcon /> : <FileCopyIcon />}
          onClick={(e) => {
            e.preventDefault();
            navigator.clipboard.writeText(
              `http://si.asn.i2/webtop/drl/objectId/${letter.siv2}`
            );
            setCopyTooltip([false, false, false, false].slice(0,k).concat([true]).concat([false, false, false, false].slice(k,3)));
            setTimeout(() => setCopyTooltip([false, false, false, false]), 1500);
          }}
          title="Ouvrir dans le SIv2"
          href={`http://si.asn.i2/webtop/drl/objectId/${letter.siv2}`}
          aria-label="ouvrir dans le SIv2"
        >      SIv2
          <Snackbar
            open={copyTooltip[k]}
            anchorOrigin={{
              vertical: "bottom",
              horizontal: "center",
            }}
            message={"Lien Siv2 copié dans le presse-papier"}
            action={null}
          />
        </Button>
       </StyledTableCell>
    </TableRow>
    )
  );

  lettersRows = lettersRows?.slice(0,4); // display only the first rows of the table
  return (
    <TableContainer>
      <Table aria-label="simple table">
        {tableHead}
        <TableBody>{lettersRows}</TableBody>
      </Table>
    </TableContainer>
  );
}
