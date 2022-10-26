import React from "react";
//import {CombinedCompletionResult as Option} from "../hooks/UseCombinedCompletions";


import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@material-ui/core";

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

type SummaryType = {
    "Mots-clefs": string;
    "Période recherchée": number[];
    "Résultats": number | string;
    "Site recherché": string[];
    "Exploitant recherché": string[];
    "Thème recherché": string[];
    "Secteur recherché": string[]
}

export default function WatchTable({
    summaries,
}: {
    summaries: SummaryType[];
}) {

    if (!summaries || summaries.length === 0){
        return (
            <span></span>
        )
    }

  const tableHead = (
    <TableHead>
      <TableRow>
        <StyledTableCell align="left">Mots-clefs</StyledTableCell>
        <StyledTableCell align="left">Période</StyledTableCell>
        <StyledTableCell align="left">Résultats</StyledTableCell>
        <StyledTableCell align="left">Site</StyledTableCell>
        <StyledTableCell align="left">Thème</StyledTableCell>
        <StyledTableCell align="left">Secteur</StyledTableCell>
      </TableRow>
    </TableHead>
  );

  let tableRows = summaries?.map((summary: SummaryType) => (
    <TableRow>
        <StyledTableCell align="left">{summary["Mots-clefs"]}</StyledTableCell>
        <StyledTableCell align="left">{summary["Période recherchée"].join("-")}</StyledTableCell>
        <StyledTableCell align="left">{summary["Résultats"]}</StyledTableCell>
        <StyledTableCell align="left">{summary["Site recherché"]}</StyledTableCell>
        <StyledTableCell align="left">{summary["Thème recherché"]}</StyledTableCell>
        <StyledTableCell align="left">{summary["Secteur recherché"]}</StyledTableCell>
    </TableRow>
 
    )
  );

  return (
    <TableContainer>
      <Table aria-label="table summary">
        {tableHead}
        <TableBody>{tableRows}</TableBody>
      </Table>
    </TableContainer>
  );
}
