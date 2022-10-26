import React from "react";

import { useLocation } from "react-router-dom";

import { Box, Container, Typography, Grid, Button } from "@material-ui/core";

import Skeleton from "@material-ui/lab/Skeleton";

import CategorySelector from "../components/CategorySelector";
import LetterContent from "./LetterContent";
import LetterMenu from "./LetterMenu";
import { useLinkStyles } from "./Links";
import { computeTopicsList } from "./CategoryDisplay";

import { Rechercher } from "../Pages";

import useNavigation from "../navigation/Utils";

import useSearchRequest from "../contexts/Search";

import { OpenSIV2, OpenPDF } from "../components/LetterButtons";

import useHydratedLetter from "../hooks/UseHydratedLetters";
import HydratedLetter from "../models/HydratedLetter";

function LetterActions({ letter }: { letter: HydratedLetter }) {
  const { goToPage } = useNavigation();
  return (
    <Grid container justify="center" spacing={1}>
      <Grid item>
        <Button color="primary" onClick={() => goToPage(Rechercher, undefined)}>
          Retour à ma recherche
        </Button>
      </Grid>
      <Grid item>
        <OpenSIV2
          idLetter={letter.id_letter}
          name={letter.name}
          siv2={letter?.metadata_si?.doc_id}
        />
      </Grid>
      <Grid item>
        <OpenPDF idLetter={letter.id_letter} name={letter.name} />
      </Grid>
    </Grid>
  );
}



function useQuery() {
  return new URLSearchParams(useLocation().search);
}

function Observe() {
  const query = useQuery();
  const linkStyles = useLinkStyles();
  const { filters } = useSearchRequest();

  const disabledClasses = [
    linkStyles.section,
    linkStyles.demand,
    linkStyles.sentence,
    linkStyles.leaf,
  ];
  const activatedClasses = [
    linkStyles.activatedSection,
    linkStyles.activatedDemand,
    linkStyles.activatedSentence,
    linkStyles.activatedLeaf,
  ];

  const { data, error } = useHydratedLetter(query.get("id_letter"));

  const [selectedCategories, setSelectedCategories] = React.useState<
    Set<string>
  >(new Set(filters.topics));


  const addSubcategories = React.useCallback(
    (cats: string[]) =>
      setSelectedCategories(
        (selectedCategories) =>
          new Set([...cats, ...Array.from(selectedCategories)])
      ),
    []
  );

  const delSubcategories = React.useCallback((cats: string[]) => {
    const remove = new Set(cats);
    setSelectedCategories(
      (selectedCategories) =>
        new Set(Array.from(selectedCategories).filter((v) => !remove.has(v)))
    );
  }, []);


  const initialSelection = React.useMemo(() => {
    if (data) {
      const topics = data.content.map((t) => computeTopicsList(t)).flat();
      return new Set([...filters.topics, ...topics]);
    } else {
      return new Set(filters.topics);
    }
  }, [filters.topics, data]);


  if (error) {
    if (error.status && error.status === 404) {
      return (
        <Container>
          <Typography> La lettre n'existe pas </Typography>
        </Container>
      );
    } else {
      return (
        <Container>
          <Typography>
            Une erreur est survenue ({JSON.stringify(error)})
          </Typography>
        </Container>
      );
    }
  }

  if (!query.get("id_letter")) {
    return (
      <Container>
        <Box p={3} m={4}>
          <Typography>
            Faites une recherche pour trouver une lettre à observer
          </Typography>
        </Box>
      </Container>
    );
  } else {
    return (
      <Box p={3}>
        <Grid container direction="row">
          <Grid item sm={12}>
            <Typography variant="h4">
              {data?.name ||
                `Observation de la lettre ${query.get("id_letter")}`}
            </Typography>
          </Grid>
          <Grid item sm={12} lg={3}>
            {data && <LetterActions letter={data} />}
            <CategorySelector
              restrictToCodes={initialSelection}
              addItem={addSubcategories}
              deleteItem={delSubcategories}
              selectedSubcategoryCodes={new Set(selectedCategories)}
            />
          </Grid>
          <Grid item sm={9} lg={6}>
            <Box p={2}>
              {data?.content ? (
                <LetterContent
                  letter={data}
                  prefix="root-letter"
                  selectedCategories={selectedCategories}
                  activatedClasses={activatedClasses}
                  disabledClasses={disabledClasses}
                />
              ) : (
                <Skeleton variant="rect" height="10em" />
              )}
            </Box>
          </Grid>
          <Grid
            item
            sm={3}
            style={{
              position: "sticky",
              top: "4rem",
              alignSelf: "start",
              maxHeight: "calc(100vh - 9rem)",
              overflowY: "auto",
            }}
          >
            {data?.content ? (
              <LetterMenu
                letter={data}
                prefix="root-letter"
                activatedClasses={activatedClasses}
                disabledClasses={disabledClasses}
              />
            ) : (
              <Skeleton variant="rect" height="30em" />
            )}
          </Grid>
        </Grid>
      </Box>
    );
  }
}

export default Observe;
