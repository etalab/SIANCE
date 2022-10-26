import React from "react";

import {
  Button,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from "@material-ui/core";

import conf from "../config.json";

import useSearchRequest, { SearchRequest } from "../contexts/Search";
import { sendUserLog } from "../api/Api";
import useDownloadToken from "../hooks/UseDownloadToken";
import useSearchResponse, {
  LettersResult,
  DemandsResult,
} from "../hooks/UseSearchResponse";

type ExportDialogMessageProps = {
  request: SearchRequest;
  mode: number;
};
function ExportDialogMessage({ request, mode }: ExportDialogMessageProps) {
  const { data } = useSearchResponse<LettersResult | DemandsResult>(
    mode,
    request,
    1
  );

  if (data) {
    return (
      <Typography>
        Le fichier que vous allez télécharger contient{" "}
        <span style={{ textDecoration: "underline" }}>
          {data && data.total} lignes
        </span>
        , voulez-vous le télécharger malgré-tout ?
      </Typography>
    );
  } else {
    return (
      <Typography>Estimation de la taille du fichier en cours...</Typography>
    );
  }
}

type ExportButtonDialogProps = {
  setOpen: (v: boolean) => void;
  request: SearchRequest;
  mode: number;
};

function ExportButtonDialog({
  request,
  mode,
  setOpen,
}: ExportButtonDialogProps) {
  const selectedIndex = mode === 2 ? "demands" : "letters";
  const { data: temporaryDownloadToken } = useDownloadToken();
  const url = `${conf.api.url}/export/search/${selectedIndex}?sentence=${
    request.sentence
  }&daterange=${encodeURI(
    JSON.stringify(request.daterange)
  )}&filters=${encodeURI(JSON.stringify(request.filters))}&token=${
    temporaryDownloadToken?.download_token
  }`;

  return (
    <>
      <DialogTitle>Télécharger un export Excel</DialogTitle>
      <DialogContent>
        <ExportDialogMessage request={request} mode={mode} />
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setOpen(false)}>Annuler</Button>
        <Button
          aria-label="excel-search-button"
          size="small"
          disabled={!temporaryDownloadToken}
          onClick={() => {
            sendUserLog(
              "OPEN_XLSX",
              JSON.stringify({
                sentence: request.sentence,
                daterange: request.daterange,
                filters: request.filters,
              })
            );
            setOpen(false);
          }}
          href={url}
          color="primary"
        >
          Télécharger
        </Button>
      </DialogActions>
    </>
  );
}

type ExportButtonProps = {
  mode: number;
  text?: string;
};

export const withExport = <P extends {}>(
  WrappedComponent: React.ComponentType<{ onClick: () => void }>
) => ({ mode, text, ...props }: ExportButtonProps & P) => {
  const [open, setOpen] = React.useState<boolean>(false);
  const { dispatch, ...searchRequest } = useSearchRequest();

  return (
    <>
      <WrappedComponent onClick={() => setOpen(!open)} {...props} />
      <Dialog open={open} onClose={() => setOpen(false)}>
        {open ? (
          <ExportButtonDialog
            setOpen={setOpen}
            mode={mode}
            request={searchRequest}
          />
        ) : null}
      </Dialog>
    </>
  );
};

function ExportButton({ mode, text, ...props }: ExportButtonProps) {
  const [open, setOpen] = React.useState<boolean>(false);
  const { dispatch, ...searchRequest } = useSearchRequest();

  return (
    <>
      <Button onClick={() => setOpen(!open)} {...props}>
        {text || "Exporter"}
      </Button>
      <Dialog open={open} onClose={() => setOpen(false)}>
        {open ? (
          <ExportButtonDialog
            setOpen={setOpen}
            mode={mode}
            request={searchRequest}
          />
        ) : null}
      </Dialog>
    </>
  );
}

export default ExportButton;
