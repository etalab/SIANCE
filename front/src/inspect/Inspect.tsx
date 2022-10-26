import React from "react";

import { Paper, Typography, Box, Grid } from "@material-ui/core";

import LastCresWithSiteName from "../dashboard/LastCresWithSiteName";
import { ReplaceFilterToContext } from "../components/FilterAutocomplete";
//import { ReplaceFilterNoContext } from "../components/FilterAutocomplete";
import useSearchRequest, {
  ConstraintType,
  InterlocutorName,
  SiteName,
  Theme,
} from "../contexts/Search";
//import {CombinedCompletionResult as Option} from "../hooks/UseCombinedCompletions";

import InspectionTable from "./InspectionTable";


function InterlocutorFilter(
 // {interlocutors, setInterlocutors}:
 // {interlocutors: Option[], setInterlocutors: (interlocutors: Option[])=>void},
){
  return (
    <ReplaceFilterToContext
      filters={[SiteName, InterlocutorName]}
    />
  )

  /*
  return (
    <ReplaceFilterNoContext
      localValues={interlocutors}
      setLocalValues={setInterlocutors}
      filtersForAutocomplete={[SiteName, InterlocutorName]}
      title="Les inspections de cet interlocuteur"
  />
  );
  */
}

function ThemeFilter(
/*{
  themes, setThemes
} : {
  themes:Option[], setThemes: (themes: Option[])=>void
}*/
) {

  return (
    <ReplaceFilterToContext
      filters={[Theme]}
    />
  )
    /*
  
  return (
    <ReplaceFilterNoContext 
      localValues={themes}
      setLocalValues={setThemes}
      filtersForAutocomplete={[Theme]}
      title="Les inspections sur ce thème"
    />
  );
  */
}

function Inspection(
  {
    filters,
 //   values
  }: {
    filters: ConstraintType[],
 //   values: Option[]
  }
) {
  const { filters: selectedFilters } = useSearchRequest();
  const filter = filters.find(filter => selectedFilters[filter.api].length > 0);  // constraintType or undefined
  const filterContent = filter ? selectedFilters[filter.api] : undefined;


  if (filterContent && filter) {
    const title = `Les dernières inspections sur le même ${filter.name.toLowerCase()} (${filterContent})`;

    return (
      <Paper elevation={3}>
        <Box pl={2}>
          <Typography variant="h6" color="primary">
            {title}
          </Typography>
        </Box>
        <InspectionTable filter={filter} />
      </Paper>
    );
  } else {
    const title = filter? `Veuillez préciser un ${filter.name.toLowerCase()}`: `Veuillez préciser un ${filters[0].name.toLowerCase()}`;
    return (
      <Paper elevation={3}>
        <Box pl={2}>
          <Typography variant="h6" color="primary">
            {title}
          </Typography>
        </Box>
      </Paper>
    );
  }
}

function ESR(
  /*
{
  selection
}: {
 selection?: Option[]
} */
) {
  const title =
    "Les derniers événements significatifs de cet entreprise/établissement";
  return (
    <Paper elevation={3}>
      <Box pl={2}>
        <Typography variant="h6" color="primary">
          {title}
        </Typography>
      </Box>
      <LastCresWithSiteName />
    </Paper>
  );
}


function InspectPage() {
  const { filters } = useSearchRequest();
 // const [interlocutors, setInterlocutors] = React.useState<Option[]>([]);
//  const [themes, setThemes] = React.useState<Option[]>([]);

  return (
    <Box p={2}>
      <Typography variant="h4" color="primary">
        Préparation d'inspection
      </Typography>
      <Typography variant="body2">
        Cette page permet de retrouver les dernières inspections sur votre interlocuteur ou votre thème d'intérêt. Vous pouvez également voir les derniers événements significatifs qui se sont produits chez cet exploitant.
      </Typography>
      <Grid container direction="column" spacing={2}>
        <Grid item>
          <Grid container direction="row" spacing={9}>
            <Grid item xs={6}>
              <InterlocutorFilter  />
            </Grid>
          </Grid>
        </Grid>
        {filters.interlocutor_name.length > 0 || filters.site_name.length > 0 ? (
          <Grid item>
            <Inspection filters={[InterlocutorName, SiteName]}/>
          </Grid>
        ):undefined
        }
        <Grid item>
          <Grid container direction="row" spacing={9}>
            <Grid item xs={6}>
              <ThemeFilter />
            </Grid>
          </Grid>
        </Grid>
        {filters.theme.length > 0 ? (
          <Grid item>
            <Inspection filters={[Theme]}/>
          </Grid>
        ):undefined
        /*
        themes.length > 0 ? (
          <Grid item>
            <Inspection filters={[Theme]} values={themes}/>
          </Grid>
        ) : undefined
        */
        }
        {filters.interlocutor_name.length > 0 || filters.site_name.length > 0 ? (
          <Grid item>
            <ESR/>
          </Grid>
        ):undefined
        }
        {
        /*interlocutors.length > 0 ? (
          <>
            <Grid item>
              <ESR selection={interlocutors}/>
            </Grid>
          </>
        ) : undefined
        */
        }
      </Grid>
    </Box>
  );
}

export default InspectPage;
