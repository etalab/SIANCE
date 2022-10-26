import React from "react";

import { Grid, Typography, Button, makeStyles } from "@material-ui/core";

import CategorySelector from "../components/CategorySelector";
import useOntology from "../hooks/UseOntology";
import useMLStatus from "../hooks/UseMLStatus";


function AnnotationPrerun({
  category,
  setCategory,
  selectedCodes,
  setSelectedCodes,
  onValidate,
}: {
  category: string;
  setCategory: (category: string) => void;
  selectedCodes: Set<string>;
  setSelectedCodes: (selectedCodes: Set<string>) => void;
  onValidate: (codes: Set<string>) => void;
}) {
  const { data: ontology } = useOntology();
  const { data: mlStatus } = useMLStatus();

  const intersect = function(array1: Array<string>, array2: Array<string>) {
    return array1.filter((value: string) => array2.includes(value)).length > 0
  }
  const recognizeCategory = function(ontology: any, subcategories: string[]) {
    let newCategoryArr = (ontology || []).map((o: any) => intersect(o.subcategories.map((x: any)=>x.subcategory), subcategories) ? o.category : undefined).filter(Boolean) as string[]
    let newCategory = (newCategoryArr[0] ? newCategoryArr[0] : undefined) || category
    setCategory(newCategory)
    return newCategory
  }
  const filterSubcategories = function(ontology: any, category: string, codes: Set<string>) {
    return (ontology || []).flatMap((o: any) => {
      let subcategories = o.subcategories.map((x: any)=>x.subcategory).filter((e: string)=>codes.has(e))
      return (o.category === category) ? subcategories : undefined
    }).filter(Boolean) as string[]
  }
  const documentsCount = mlStatus?.total_letters || 0;
  const annotationsCount = mlStatus?.total_annotations || 0;
  const annotatedDocumentsCount = mlStatus?.total_annotated_letters || 0;

  const addItem = (codes: string[]) => {
    // it is possible to selected several subcategories, provided they all belong to the same category
    // selecting a subactegory automatically unselects subcategories from other categories
    const newCategory = recognizeCategory(ontology, codes)
      // among previously selected codes, keep only the ones where category matches the last selected category
    let previousCodesNewCategory = filterSubcategories(ontology, newCategory, selectedCodes)
    setSelectedCodes(new Set([...codes, ...previousCodesNewCategory]));
  };

  const delItem = (codes: string[]) => {
    const delSet = new Set(codes);
    setSelectedCodes(
      new Set(Array.from(selectedCodes).filter((x) => !delSet.has(x)))
    );
  };


  const validation = () => {
    // by construction, only one category can be selected simultaneously, and function category -> subcategory is injective
    onValidate(selectedCodes);
  };


  const useStyles = makeStyles((theme) => ({
    button: {
      background: theme.palette.primary.dark,
      color: "white",
      width: "100%"
    }
  }))
  return (
    <Grid container>
      <Grid container item sm={12}>
        <Grid item sm={4}>
          <Typography variant="h6">Lettres de suites et annotations</Typography>
        </Grid>
        <Grid item sm={1}>
        </Grid>
        <Grid container item sm={7}>
          <Grid item sm={12}>
            <Typography variant="h6">{documentsCount} lettres publiées</Typography>
          </Grid>
          <Grid item sm={12}>
            <Typography variant="h6">
              dont {annotatedDocumentsCount} lettres partiellement annotées
            </Typography>
          <Grid item sm={12}>
            <Typography variant="h6">Pour un total de {annotationsCount} phrases annotées</Typography>
          </Grid>
          </Grid>
        </Grid>
      </Grid>
      <Grid container item sm={12}>
        <Grid item sm={4}>
          <Typography variant="h6">Priorités d'annotation</Typography>
          <Typography variant="body2">Choisir une catégorie à annoter en priorité</Typography>

        </Grid>
        <Grid item sm={1}>
        </Grid>
        <Grid item sm={7}>
          <CategorySelector
            selectedSubcategoryCodes={selectedCodes}
            addItem={addItem}
            deleteItem={delItem}
          />
        </Grid>
      </Grid>
      <Grid container item sm={12}>
        <Grid item sm={4}>
          <Typography variant="h6">
            Paramètres
          </Typography>
          <Typography variant="body2">Les annotations sont majoritairement issues de la priorité choisie</Typography>

        </Grid>
        <Grid item sm={1}>
        </Grid>
        <Grid container item sm={7}>
          <Grid item sm={12}>
            <Typography variant="h6">La session comprendra 20 propositions à annoter</Typography>
          </Grid>
        </Grid>
      </Grid>
      <Grid item sm={1}>
        </Grid>
      <Grid item sm={12}>
        <Button className={useStyles().button} onClick={validation}>
          démarrer
        </Button>
      </Grid>
    </Grid>
  );
}

export default AnnotationPrerun;
