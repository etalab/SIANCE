import React from "react";
import { Typography, CircularProgress } from "@material-ui/core";

import useMLStatus from "../hooks/UseMLStatus";

function MLStatus() {
  const { data } = useMLStatus();

  return data ? (
    <Typography variant="body2">
      Il y a {data.total_annotated_letters} lettres annotées sur{" "}
      {data.total_letters}. En moyenne, le modèle fait{" "}
      {(data.total_predictions / (data.total_letters || 1)).toFixed(2)}{" "}
      prédictions par lettre.
    </Typography>
  ) : (
    <CircularProgress />
  );
}

export default MLStatus;
