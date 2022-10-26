import React from "react";

import SpeedDial from "@material-ui/lab/SpeedDial";
import SpeedDialIcon from "@material-ui/lab/SpeedDialIcon";
import SpeedDialAction from "@material-ui/lab/SpeedDialAction";

import {
  Dialog,
  DialogTitle,
  DialogContent,
  Box,
  TextField,
  Divider,
  Typography,
  DialogActions,
  Button,
  makeStyles,
} from "@material-ui/core";

import FileCopyIcon from "@material-ui/icons/FileCopy";
import FileDownloadIcon from "@material-ui/icons/CloudDownload";
import SaveIcon from "@material-ui/icons/Save";
import CheckIcon from "@material-ui/icons/Check";
import HelpIcon from "@material-ui/icons/Help";

import { useUserConfig } from "../authentication/Utils";
import useSavedSearches from "../hooks/UseUserSearch";

import { useInspectDispatchDisplay } from "./contexts/Displays";
import useSearchRequest, { constraintList } from "../contexts/Search";
import { useModeLetters } from "./contexts/Modes";
import { withExport } from "../components/Export";

const useStyles = makeStyles((theme) => ({
  floatingAction: {
    position: "absolute",
    bottom: theme.spacing(2),
    right: theme.spacing(4),
  },
}));

function CopyURLSpeedAction(props: any) {
  const [copyTooltip, setCopyTooltip] = React.useState<boolean>(false);

  return navigator.clipboard && navigator.clipboard.writeText ? (
    <SpeedDialAction
      icon={copyTooltip ? <CheckIcon /> : <FileCopyIcon />}
      tooltipTitle="Copier ma recherche"
      aria-label="save-search-speed-action"
      onClick={() => {
        navigator.clipboard.writeText(window.location.toString());
        setCopyTooltip(true);
        setTimeout(() => setCopyTooltip(false), 1500);
      }}
      title="Copier la recherche dans le presse-papier"
      {...props}
    />
  ) : null;
}

function HelpSpeedAction(props: any) {
  const dispatchDisplay = useInspectDispatchDisplay();
  return (
    <SpeedDialAction
      icon={<HelpIcon />}
      title="Aide"
      tooltipTitle="aide"
      aria-label="help-search-button"
      onClick={() => dispatchDisplay({ type: "SHOW_HELP" })}
      {...props}
    />
  );
}

function SaveMySearchSpeedAction(props: any) {
  const [isOpen, setOpen] = React.useState<boolean>(false);
  return (
    <>
      <SpeedDialAction
        icon={<SaveIcon />}
        tooltipTitle="super action"
        aria-label="save-search-button"
        onClick={() => setOpen(true)}
        title="Ajouter la recherche à mon profil"
        //startIcon={<FileCopyIcon />}
        {...props}
      >
        Engeristrer la recherche
      </SpeedDialAction>
      <Dialog open={isOpen} onClose={() => setOpen(false)}>
        <SaveMySearchDialogContent handleClose={() => setOpen(false)} />
      </Dialog>
    </>
  );
}

function SaveMySearchDialogContent({
  handleClose,
}: {
  handleClose: () => void;
}) {
  const { data: userConfig } = useUserConfig();
  const { filters, sentence, daterange, sorting } = useSearchRequest();

  const { data: savedSearches, handleSave } = useSavedSearches();

  const [name, setName] = React.useState<string>("");

  const isSaved =
    savedSearches !== undefined &&
    savedSearches.some((v) => v.stored_search.name === name);

  const isValid = !isSaved && name.trim() !== "";

  const filtersTexts = constraintList
    .filter((constraint) => filters[constraint.api].length > 0)
    .map((constraint) => constraint.name);

  return (
    <>
      <DialogTitle>Engeristrer cette recherche</DialogTitle>
      <DialogContent>
        <Box p={1}>
          <TextField
            label="Nom de la recherche"
            placeholder="Liste 1"
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={name !== "" && !isValid}
          />
        </Box>
        <Divider />
        <Box p={1}>
          <Typography variant="body1">
            Enregistrement de la liste{" "}
            {name !== "" ? (
              <Typography color="primary" component="span">
                {name}
              </Typography>
            ) : (
              <Typography color="secondary" component="span">
                nom à déterminer
              </Typography>
            )}{" "}
            {sentence.trim() === "" ? (
              <>qui ne recherche pas en plein texte</>
            ) : (
              <>
                qui recherche le texte
                <Typography color="secondary" component="span">
                  {sentence}
                </Typography>
              </>
            )}{" "}
            {filtersTexts.length === 0 ? (
              "."
            ) : filtersTexts.length === 1 ? (
              <>
                et filtre selon le critère{" "}
                <Typography color="primary" component="span">
                  {filtersTexts.join(", ")}
                </Typography>
                .
              </>
            ) : (
              <>
                et filtre en utilisant les critères{" "}
                <Typography color="primary" component="span">
                  {filtersTexts.join(", ")}
                </Typography>
                .
              </>
            )}
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Annuler</Button>
        <Button
          aria-label="save"
          size="small"
          variant="outlined"
          disabled={!userConfig || !isValid}
          onClick={() => {
            userConfig &&
              handleSave({
                id_user: userConfig.user.id_user,
                query: { filters, sentence, daterange, sorting },
                name: name,
              }) &&
              handleClose();
          }}
          color="primary"
        >
          {isSaved ? "Existe déjà" : "Enregistrer"}
        </Button>
      </DialogActions>
    </>
  );
}

const ExportSpeed = withExport(SpeedDialAction);
function ExportExcelSpeedAction(props: any) {
  const { letters } = useModeLetters() as any;
  return (
    <ExportSpeed
      mode={letters}
      {...props}
      icon={<FileDownloadIcon />}
      tooltipTitle="Exporter ma recherche en excel"
      aria-label="save-search-speed-action"
    />
  );
}

function InspectSpeedDial() {
  const styles = useStyles();
  const [open, setOpen] = React.useState(false);
  return (
    <SpeedDial
      open={open}
      onClose={() => setOpen(false)}
      onOpen={() => setOpen(true)}
      ariaLabel="SpeedDial example"
      hidden={false}
      icon={<SpeedDialIcon />}
      className={styles.floatingAction}
    >
      <CopyURLSpeedAction />
      <ExportExcelSpeedAction />
      <SaveMySearchSpeedAction />
      <HelpSpeedAction />
    </SpeedDial>
  );
}

export default InspectSpeedDial;
