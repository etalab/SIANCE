import React from "react";

import { ELetter } from "../models/Letter";
import { SearchFilters } from "../contexts/Search";
import { Typography } from "@material-ui/core";

type LetterSummaryContentProps = {
  letter: ELetter;
  filters: SearchFilters;
  domains: string;
  summaryClass: string;
  keywordClass: string;
};

function LetterSummaryContentEDF({
  letter,
  summaryClass,
  keywordClass,
  domains,
}: LetterSummaryContentProps) {
  const trigrams = Array.from(new Set(letter.equipments_trigrams)).join(", ");
  const isotopes = Array.from(new Set(letter.isotopes)).join(", ");

  if (domains.indexOf(", Centrale nucléaire") > -1) {
    let idx = domains.indexOf(", Centrale nucléaire")
    domains = domains.slice(0, idx) + domains.slice(idx+20)
  } else if (domains.indexOf("Centrale nucléaire") > -1) {
    let idx = domains.indexOf("Centrale nucléaire")
    domains = domains.slice(0, idx) + domains.slice(idx+18)
  }
  return (
    <Typography className={summaryClass}>
      Cette inspection s'est terminée en{" "}
      <span className={keywordClass}>
        {new Date(letter.date).toLocaleDateString("fr-FR", {
          year: "numeric",
          month: "long",
        })}
      </span>{" "}
      à{" "}
      <span className={keywordClass}>
        {[letter.site_name, letter.complementary_site_name]
          .filter((x) => x)
          .join(", ")}
      </span>{" "}
      {domains !== "" ? (
        <>
          sur les domaines suivants:{" "}
          <span className={keywordClass}>{domains}</span>
        </>
      ) : null}
      . L'inspection avait pour thème{" "}
      <span className={keywordClass}>{letter.theme}</span>.
      {trigrams !== "" ? (
        <p>
          {letter.equipments_trigrams.length === 1
            ? "\n Système EDF mentionné"
            : "\n Systèmes EDF mentionnés"}
          :<span className={keywordClass}> {trigrams}</span>.
        </p>
      ) : null}
      {isotopes !== "" ? (
       <p>
          {letter.isotopes.length === 1
            ? "\n Isotope mentionné"
            : "\n Isotopes mentionnés"}
          :<span className={keywordClass}> {isotopes}</span>.
        </p>
       ) : null}
    </Typography>
  );
}

function LetterSummaryContentLUDD({
  letter,
  summaryClass,
  keywordClass,
  domains,
}: LetterSummaryContentProps) {
  let names = [
    letter.interlocutor_name,
    ...letter.site_name,
    letter.complementary_site_name,
    ...letter.natures
  ];
  let simplifyCEAName = (name: string) => {
    if (name && (name.toUpperCase() === "AGENCE NAT GESTION DECHETS RADIOACTIFS")) {
      return "ANDRA"
    } else if (name && (name.toUpperCase() === "COMMISSARIAT A L' ENERGIE ATOMIQUE ET AUX ENERGIES ALTERNATIVES")){
      return "CEA"
    } else {
      return name
    }
  } 
  const isotopes = Array.from(new Set(letter.isotopes)).join(", ");

  return (
    <Typography className={summaryClass}>
      Cette inspection <span className={keywordClass}>LUDD</span> s'est terminée
      en{" "}
      <span className={keywordClass}>
        {new Date(letter.date).toLocaleDateString("fr-FR", {
          year: "numeric",
          month: "long",
        })}
      </span>{" "}
      à{" "}
      <span className={keywordClass}>{names.map(simplifyCEAName).filter((x) => x).join(", ")}</span>{" "}
      {domains !== "" ? (
        <>
          sur les domaines suivants:{" "}
          <span className={keywordClass}>{domains}</span>
        </>
      ) : null}
      . L'inspection avait pour thème{" "}
      <span className={keywordClass}>{letter.theme}</span>.
      {isotopes !== "" ? (
        <p>
          {letter.isotopes.length === 1
            ? "\n Isotope mentionné"
            : "\n Isotopes mentionnés"}
          :<span className={keywordClass}> {isotopes}</span>.
        </p>
      ) : null}
    </Typography>
  );
}

function LetterSummaryContentDefault({
  letter,
  summaryClass,
  keywordClass,
  domains,
}: LetterSummaryContentProps) {
  // for non-INB letters, like (non-INB) TSR letters, NP letters, letters whose sectors has not been detected
  const isotopes = Array.from(new Set(letter.isotopes)).join(", ");
  const names = [
    letter.interlocutor_name,
    ...letter.site_name,
    letter.complementary_site_name,
  ]
  let simplifyAPHPname = (name: string) => {
    return name && (name.toUpperCase() === "ASSISTANCE PUBLIQUE HOPITAUX DE PARIS")? "APHP": name
  } 
    return (
    <Typography className={summaryClass}>
      Cette inspection s'est terminée en{" "}
      <span className={keywordClass}>
        {new Date(letter.date).toLocaleDateString("fr-FR", {
          year: "numeric",
          month: "long",
        })}
      </span>
      . Elle a été réalisée par{" "}
      <span className={keywordClass}>{letter.pilot_entity}</span> et concerne{" "}
      <span className={keywordClass}>
        {
          names.map(simplifyAPHPname)
          .filter((x) => x)
          .join(", ")}
      </span>{" "}
      {domains !== "" ? (
        <>
          sur les domaines suivants:{" "}
          <span className={keywordClass}>{domains}</span>
        </>
      ) : null}
      . L'inspection avait pour thème{" "}
      <span className={keywordClass}>{letter.theme}</span>.
      {isotopes !== "" ? (
        <p>
          {letter.isotopes.length === 1
            ? "\n Isotope mentionné"
            : "\n Isotopes mentionnés"}
          :<span className={keywordClass}> {isotopes}</span>.
        </p>
      ) : null}
    </Typography>
  );
}

/**
 * Dispatch Card to select the right
 * way to display the inspection.
 *
 * This mainly selects between REP(EDF), LUDD and NPX.
 *
 */
function LetterSummaryContent(props: LetterSummaryContentProps) {
  if (
    props.letter.interlocutor_name === "ELECTRICITE DE FRANCE" ||
    props.letter.sectors.some((x) => x === "REP")
  ) {
    return <LetterSummaryContentEDF {...props} />;
  } else if (props.letter.sectors.some((x) => x === "LUDD")) {
    return <LetterSummaryContentLUDD {...props} />;
  } else {
    return <LetterSummaryContentDefault {...props} />;
  }
}

export default LetterSummaryContent;
