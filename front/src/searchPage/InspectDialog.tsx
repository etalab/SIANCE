import React from "react";

import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  DialogContentText,
  List,
  ListItem,
  ListItemText,
  Button,
} from "@material-ui/core";

import { parse, match } from "../lib/StringMatch";

import useInspectDisplay, {
  useInspectDispatchDisplay,
} from "./contexts/Displays";
import useSearchRequest from "../contexts/Search";

import { ErrorNotification } from "../Errors";
import { OpenPDF, OpenSIV2, OpenObserve } from "../components/LetterButtons";
import useExplainLetter from "../hooks/UseExplainLetter";
import useSuggestResponse from "../hooks/UseSuggestResponse";

export function SelectedDemandDialog() {
  const { showParasDialog: showDialog, selectedDemand } = useInspectDisplay();
  const dispatch = useInspectDispatchDisplay();

  function quit() {
    dispatch({ type: "QUIT_PREVIEW" });
  }

  if (!selectedDemand) {
    return <></>;
  }

  return (
    <Dialog
      onClose={quit}
      aria-labelledby="help-search"
      open={showDialog}
      scroll="paper"
      fullWidth={true}
    >
      <DialogTitle color="primary" id="paras-search-title">
        Contexte de la demande {selectedDemand._source.name}
      </DialogTitle>
      <DialogContent style={{ padding: 10 }}>
        La synthèse de la lettre dont provient la demande:
        <DialogContentText style={{ whiteSpace: "pre-line" }}>
          {selectedDemand._source.summary.trim()}
        </DialogContentText>
        Le texte de la demande:
        <DialogContentText style={{ whiteSpace: "pre-line" }}>
          {selectedDemand._source.content.trim()}
        </DialogContentText>
        Voici quelques extraits de paragraphes correspondants à la recherche:
        <DialogContentText>
          {selectedDemand.highlight.map((paragraph) => (
            <span key={paragraph} style={{ display: "inline-block" }}>
              {paragraph.split("###").map((content, i) => {
                if (i % 2 === 0) {
                  return <React.Fragment key={i}>{content}</React.Fragment>;
                } else {
                  return (
                    <em
                      key={i}
                      style={{
                        color: "orange",
                        fontWeight: 700,
                      }}
                    >
                      {content}
                    </em>
                  );
                }
              })}
            </span>
          ))}
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <OpenSIV2
          idLetter={selectedDemand.doc_id}
          name={selectedDemand._source.name}
          siv2={selectedDemand._source.siv2}
        />
        <OpenPDF
          idLetter={selectedDemand.doc_id}
          name={selectedDemand._source.name}
        />
        <OpenObserve
          idLetter={selectedDemand.doc_id}
          name={selectedDemand._source.name}
        >
          Ouvrir dans SIANCE
        </OpenObserve>
        <Button onClick={quit} variant="outlined" color="primary">
          Fermer
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function findWords(desc: any): string[] {
  if (desc && desc.description) {
    if (desc.description.length > 0 && desc.description[0] === "w") {
      return desc.description.slice(
        desc.description.indexOf(":") + 1,
        desc.description.indexOf(" ")
      );
    } else {
      return desc?.details?.flatMap(findWords) || [];
    }
  } else {
    return [];
  }
}

function FullTextExplain() {
  const { sentence } = useSearchRequest();
  const { selectedLetter } = useInspectDisplay();
  const { data: explain } = useExplainLetter(sentence, selectedLetter?.doc_id);

  const found = Array.from(new Set(findWords(explain?.explanation)))
    .sort()
    .reverse()
    .join(" ");

  const matches = match(found, sentence);
  const parts = parse(found, matches);

  if (selectedLetter === undefined) {
    return <></>;
  }

  return (
    <>
      Si vous avez fait une recherche en plein-texte elle se trouve ci-après et
      les mots trouvés dans la lettre sont coloriés en orange:
      <DialogContentText>
        {parts.map((part: any, index: any) => (
          <span
            key={index}
            style={{
              color: part?.highlight ? "orange" : undefined,
              fontWeight: part?.highlight ? 900 : 400,
            }}
          >
            {part?.text}
          </span>
        ))}
      </DialogContentText>
      Voici quelques extraits de paragraphes correspondants à la recherche:
      <DialogContentText>
        {selectedLetter.highlight.map((paragraph) => (
          <span key={paragraph} style={{ display: "inline-block" }}>
            {paragraph.split("###").map((content, i) => {
              if (i % 2 === 0) {
                return <React.Fragment key={i}>{content}</React.Fragment>;
              } else {
                return (
                  <em
                    key={i}
                    style={{
                      color: "orange",
                      fontWeight: 700,
                    }}
                  >
                    {content}
                  </em>
                );
              }
            })}
          </span>
        ))}
      </DialogContentText>
    </>
  );
}

function SignificantCategories() {
  const { selectedLetter } = useInspectDisplay();
  const { data: suggestion } = useSuggestResponse("letters");

  if (selectedLetter === undefined) {
    return <></>;
  }

  const topCategories: { [key: string]: number } = {};
  selectedLetter._source.topics.forEach((topic) => {
    if (topCategories[topic]) {
      topCategories[topic] += 1;
    } else {
      topCategories[topic] = 1;
    }
  });

  const podium = Object.entries(topCategories).sort((a, b) => a[1] - b[1]);

  return (
    <List>
      {podium.slice(0, 2).map(([subcategory, count]) => (
        <ListItem>
          <ListItemText primary={subcategory} secondary={count} />
        </ListItem>
      ))}
      {suggestion?.topics.slice(0, 2).map((subcategory) => (
        <ListItem key={subcategory.value}>
          <ListItemText
            primary={subcategory.value}
            secondary={topCategories[subcategory.value] || 0}
          />
        </ListItem>
      ))}
    </List>
  );
}

export default function ParasDialog() {
  const { showParasDialog: showDialog, selectedLetter } = useInspectDisplay();
  const dispatch = useInspectDispatchDisplay();

  function quit() {
    dispatch({ type: "QUIT_PREVIEW" });
  }

  if (!selectedLetter) {
    return <></>;
  }

  if (showDialog && selectedLetter._source.name === "") {
    return (
      <ErrorNotification
        open={true}
        autoHideDuration={6000}
        message={`Une erreur est survenue, la lettre demandée n'existe pas`}
      />
    );
  }

  return (
    <Dialog
      onClose={quit}
      aria-labelledby="help-search"
      open={showDialog}
      scroll="paper"
      fullWidth={true}
    >
      <DialogTitle color="primary" id="paras-search-title">
        Pourquoi la lettre {selectedLetter._source.name} est-elle pertinente ?
      </DialogTitle>
      <DialogContent style={{ padding: 10 }}>
        <FullTextExplain />
        <SignificantCategories />
      </DialogContent>
      <DialogActions>
        <OpenSIV2
          idLetter={selectedLetter.doc_id}
          name={selectedLetter._source.name}
          siv2={selectedLetter._source.siv2}
        />
        <OpenPDF
          idLetter={selectedLetter.doc_id}
          name={selectedLetter._source.name}
        />
        <OpenObserve
          idLetter={selectedLetter.doc_id}
          name={selectedLetter._source.name}
        >
          Ouvrir dans SIANCE
        </OpenObserve>
        <Button onClick={quit} variant="outlined" color="primary">
          Fermer
        </Button>
      </DialogActions>
    </Dialog>
  );
}
