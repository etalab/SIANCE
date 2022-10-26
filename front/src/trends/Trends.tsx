import React from "react";
import { Grid, Box, Typography, CircularProgress } from "@material-ui/core";

import { VegaLite } from "react-vega";

import { ToggleSectors } from "../components/ToggleButtons";
import { ToggleModes } from "../searchPage/Types";
import SelectSystem from "./SelectSystem";
import SelectThemes from "./SelectThemes";
import systems_bubbles from "./static/_systems_bubbles.json";

import AllSystems from "./AllSystems";
import {CombinedCompletionResult as Option} from "../hooks/UseCombinedCompletions";

import CategorySelector from "../components/CategorySelector";
import useSearchRequest from "../contexts/Search";
import useTrendsTopics, { useHighlightTopics} from "../hooks/UseTrendsTopics";
import useTrendsThemes from "../hooks/UseTrendsThemes";


// import useSuggestResponse from "../hooks/UseSuggestResponse";

function SystemsBubbles() {
  return <VegaLite spec={systems_bubbles as any} />;
}

function CategoriesSelectorCustom({
  selectedCategories,
  setSelectedCategories,
  boldSubcategories
}: {
  selectedCategories: Set<string>;
  setSelectedCategories: (foo: (bar: Set<string>) => Set<string>) => void;
  boldSubcategories?: string[]
}) {
  const addSubcategories = React.useCallback(
    (cats: string[]) =>
      setSelectedCategories(
        (selectedCategories) =>
          new Set([...cats, ...Array.from(selectedCategories)])
      ),
    [setSelectedCategories]
  );

  const delSubcategories = React.useCallback(
    (cats: string[]) => {
      const remove = new Set(cats);
      setSelectedCategories(
        (selectedCategories) =>
          new Set(Array.from(selectedCategories).filter((v) => !remove.has(v)))
      );
    },
    [setSelectedCategories]
  );

  return (
    <CategorySelector
      addItem={addSubcategories}
      deleteItem={delSubcategories}
      selectedSubcategoryCodes={new Set(selectedCategories)}
      boldSubcategories={boldSubcategories}
    />
  );
}

function CategoriesTrends({
  selectedCategories,
  sectors,
}: {
  selectedCategories: Set<string>;
  sectors: Set<string>;
}) {
  const response = useTrendsTopics(selectedCategories, sectors);
  if (response.data && selectedCategories.size > 0) {
    return (
      <>
        <VegaLite spec={response.data as any} />
      </>
    );
  } else if (response.isValidating) {
    return <CircularProgress />;
  } else {
    return <div></div>;
  }
}


function ThemesTrends({
  themes,
}: {
  themes: string[];
}) {
  const response = useTrendsThemes(themes);
  if (response.data && themes.length > 0) {
    return (
      <>
        <VegaLite spec={response.data as any} />
      </>
    );
  } else if (response.isValidating) {
    return <CircularProgress />;
  } else {
    return <div></div>;
  }
}

function TopicsBlock() {
  const { filters } = useSearchRequest();
  const { data: highlightTopics} = useHighlightTopics();
  const sectors = new Set(filters.sectors);
  const [selectedCategories, setSelectedCategories] = React.useState<
    Set<string>
  >(new Set(filters.topics))


  return (
    <Box p={4}>
      <Typography variant="h4" color="primary" gutterBottom>
        Analyse de tendances pour les catégories
      </Typography>

      <Grid container direction="row" spacing={9}>
        <Grid item sm={4}>
          <CategoriesSelectorCustom
            selectedCategories={selectedCategories}
            setSelectedCategories={setSelectedCategories}
            boldSubcategories={highlightTopics}
          />
        </Grid>
        <Grid item container direction="column" sm={8} spacing={2}>
          <Grid item>
            <div>
              Sélectionnez des thématiques dans la liste ci-contre, pour
              afficher le nombre de demandes où ces thématiques ont été
              détectées dans les lettres de suite par l'algorithme
              d'intelligence artificielle.
            </div>
            <div>
              <strong>Les thématiques en gras présentent des tendances remarquables</strong> (par exemple, une raréfaction en inspection).
            </div>
            <div>
               Les nombres d'occurrences ci-dessous n'ont pas vocation
              à être repris directement, mais montrent une tendance.
            </div>

            {filters.sectors && filters.sectors.length > 0?
            <div>Restreint à : <strong>{Array.from(sectors).join(", ")}</strong></div>
            :undefined
            }
          </Grid>
          <Grid item>
            <CategoriesTrends selectedCategories={selectedCategories} sectors={sectors}/>
          </Grid>
        </Grid>
      </Grid>
    </Box>
  );
}


function ThemesBlock() {
  const [themes, setThemes] = React.useState<Option[]>([]);
  const { filters } = useSearchRequest();
  const sectors = new Set(filters.sectors);
  const interlocutors = new Set(filters.interlocutor_name.concat(filters.site_name));
  return (
    <Box p={4}>
      <Typography variant="h4" color="primary" gutterBottom>
        Analyses des tendances pour les thèmes d'inspection
      </Typography>
      {(filters.sectors && filters.sectors.length > 0) || 
          (filters.interlocutor_name && filters.interlocutor_name.length > 0) || 
          (filters.site_name && filters.site_name.length > 0) ?
        <div>Restreint à :  <strong>{Array.from(interlocutors).join(", ")}</strong>  <strong>{filters.sectors.length>0? "("+Array.from(sectors).join(", ")+")":""}</strong></div>
        :undefined
      }
      <SelectThemes themes={themes} setThemes={setThemes} />
      <ThemesTrends themes={themes.map(theme=>theme.value)}/>
    </Box>
  );

}


function SystemsTrends() {
  const [systems, setSystems] = React.useState<Option[]>([]);
  const { filters } = useSearchRequest();
  const sectors = new Set(filters.sectors);
  const interlocutors = new Set(filters.interlocutor_name.concat(filters.site_name));

  return (
    <Box p={4}>
      <Typography variant="h4" color="primary" gutterBottom>
        Analyse de tendances pour les systèmes REP
      </Typography>
      <Grid container direction="row" spacing={9}>
        <Grid item sm={4}>
          <SystemsBubbles />
        </Grid>
        <Grid item sm={8}>
        {(filters.sectors && filters.sectors.length > 0) || 
          (filters.interlocutor_name && filters.interlocutor_name.length > 0) || 
          (filters.site_name && filters.site_name.length > 0) ?
            <div>Restreint à :  <strong>{Array.from(interlocutors).join(", ")}</strong>  <strong>{filters.sectors.length>0? "("+Array.from(sectors).join(", ")+")":""}</strong></div>
            :undefined
          }
          <p>

            Le schéma ci-contre figure, pour chaque système REP, le nombre de
            lettres de suite l'ayant mentionnés depuis 2010, et le nombre
            d'événements significatifs l'ayant impacté depuis 2018. Les systèmes
            dans la partie gauche de ce schéma sont particulièrement
            remarquables, car ils ont été relativement peu mentionnés en
            inspection, mais font souvent l'objet d'événements significatifs
            EDF. La couleur du cercle montre la date médiane des inspections
            dont les lettres de suite mentionnaient le système (en se
            retreignant aux inspections entre 2010 et 2021).
          </p>
          <p>
            Vous pouvez sélectionner dans la liste ci-dessous ci-dessous
            l'histogramme des inspections sur les systèmes EDF qui vous
            intéressent. L'histogramme clair figure le nombre d'inspections
            mentionnant le système (sur la base des trigrammes détectés dans les
            lettres de suite), tandis que l'histogramme sombre montre les
            événements significatifs impactant le système. La courbe verte,
            donnée à titre indicatif, montre (après une mise à l'échelle
            arbitraire) les années où les systèmes REP ont dans leur ensemble
            davantage fait l'objet de demandes de la part de l'ASN (c'est le cas
            par exemple en 2012).
          </p>
          <SelectSystem systems={systems} setSystems={setSystems} />
        </Grid>
      </Grid>
      <Grid container direction="row" justify="space-around" spacing={2}>
        {Object.entries(AllSystems).map(([k, v]) => {
          if (systems.map(system=>system.value).some((u) => u === k)) {
            return (
              <Grid item key={k} xs={12} sm={6}>
                <VegaLite spec={v as any} />
              </Grid>
            );
          } else {
            return <></>;
          }
        })}
      </Grid>
    </Box>
  );
}

function Trends() {
  const {filters} = useSearchRequest();

  const sectors = filters.sectors;
  //const [sectors, setSectors] = React.useState<ToggleModes["sectors"]>(filters.sectors as ToggleModes["sectors"])
  return (
    <Box m={3}>

      <Grid item container sm={12} justify="center" >
        <Grid item>
          <ToggleSectors mode={sectors as ToggleModes["sectors"]}/>
        </Grid>
      </Grid>
      <TopicsBlock />
      <ThemesBlock />
      <SystemsTrends />
    </Box>
  );
}

export default Trends;
