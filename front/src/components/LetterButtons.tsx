import React from "react";

import { Button, Snackbar } from "@material-ui/core";
import PictureAsPdfIcon from "@material-ui/icons/PictureAsPdf";
import FileCopyIcon from '@material-ui/icons/FileCopy';
import CheckIcon from "@material-ui/icons/Check";

import { useHistory, useLocation } from "react-router-dom";
import { sendUserLog } from "../api/Api";
import conf from "../config.json";

import { useDispatchSeenLetters } from "../searchPage/contexts/SeenDocuments";

type LetterButtonProps = {
  siv2?: string;
  idLetter: number;
  name: string;
};

export function OpenPDF({ name, idLetter }: LetterButtonProps) {
  const dispatch = useDispatchSeenLetters();
  return (
    <Button
      size="small"
      color="primary"
      variant="outlined"
      title="Télécharger le PDF de la lettre"
      href={`${conf.api.url}/export/pdf/${name}`}
      onClick={() => {
        dispatch({ type: "add", value: idLetter });
        sendUserLog("OPEN_PDF", JSON.stringify({ pdf_id: name }));
      }}
      startIcon={<PictureAsPdfIcon />}
    >
      Télécharger
    </Button>
  );
}

export function OpenObserve({
  idLetter,
  children,
}: LetterButtonProps & { children: React.ReactNode }) {
  const history = useHistory();
  const dispatch = useDispatchSeenLetters();

  const params = new URLSearchParams(useLocation().search);
  params.set("id_letter", `${idLetter}`);

  return (
    <Button
      size="small"
      color="primary"
      title="Observer la lettre"
      href={`/find_letter?${params.toString()}`}
      onClick={(e) => {
        e.preventDefault();
        dispatch({ type: "add", value: idLetter });
        sendUserLog("OPEN_OBSERVE", JSON.stringify({ id_letter: idLetter }));
        history.push(`/find_letter?${params.toString()}`);
      }}
    >
      {children}
    </Button>
  );
}

export function OpenSIV2({ siv2, idLetter }: LetterButtonProps) {
  const dispatch = useDispatchSeenLetters();

  const [copyTooltip, setCopyTooltip] = React.useState<boolean>(false);

  return (
    <Button
      size="small"
      color="primary"
      disabled={!siv2}
      startIcon={copyTooltip ? <CheckIcon /> : <FileCopyIcon />}
      onClick={(e) => {
        e.preventDefault();
        dispatch({ type: "add", value: idLetter });
        sendUserLog("OPEN_SIV2", JSON.stringify({ id_letter: idLetter }));
        navigator.clipboard.writeText(
          `http://si.asn.i2/webtop/drl/objectId/${siv2}`
        );
        setCopyTooltip(true);
        setTimeout(() => setCopyTooltip(false), 1500);
      }}
      title="Ouvrir dans le SIv2"
      href={`http://si.asn.i2/webtop/drl/objectId/${siv2}`}
      aria-label="ouvrir dans le SIv2"
    >
      SIv2
      <Snackbar
        open={copyTooltip}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "center",
        }}
        message={"Lien Siv2 copié dans le presse-papier"}
        action={null}
      />
    </Button>
  );
}
