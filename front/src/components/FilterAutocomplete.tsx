import React from "react";

import { Grid, TextField, Divider, Badge, Typography } from "@material-ui/core";
import Autocomplete, {AutocompleteRenderInputParams} from "@material-ui/lab/Autocomplete";

import {
  parse,
  match,
  HighlightedText,
  HighlightedTextDisplay,
} from "../lib/StringMatch";


import useSearchRequest, { ConstraintType } from "../contexts/Search";

import { useDebounce } from "../api/Api";

import useCombinedCompletions, {
  CombinedCompletionResult as Option,
} from "../hooks/UseCombinedCompletions";


export function getOptionSynonym(option: Option){
  // function called before proposing options, to suggest special options 
  // when the user types some specific strings 
  const value = (option.value ? option.value: option) as string;
  switch (value.toUpperCase()) {
    case "ELECTRICITE DE FRANCE":   // option suggested to user
      return "EDF ELECTRICITE DE FRANCE" // words triggering this suggestion
    case "COMMISSARIAT A L' ENERGIE ATOMIQUE ET AUX ENERGIES ALTERNATIVES":
      return "cea COMMISSARIAT A L' ENERGIE ATOMIQUE ET AUX ENERGIES ALTERNATIVES"
    case "AGENCE NAT GESTION DECHETS RADIOACTIFS":
      return "andra AGENCE NAT GESTION DECHETS RADIOACTIFS"
    case "ASSISTANCE PUBLIQUE HOPITAUX DE PARIS":
      return "aphp ap-hp ASSISTANCE PUBLIQUE HOPITAUX DE PARIS"
    // the code below is not at the right place to modify the searchbar content...
    /*
    case "séisme":
      return "tremblement de terre séisme"
    case "incendie":
      return "feu incendie"
      */
    default: 
      return value
  }
}

function FilterOption({
  count,
  constraint,
  //selected,
  textDisplay,
}: Option & {
  textDisplay: HighlightedText[];
  selected: boolean;
}) {
  return (
    <Grid container justify="space-between" style={{ width: "90%" }}>
      <Grid item sm={12}>
        <Badge badgeContent={count} max={110} style={{ maxWidth: "100%" }}>
          <Typography>
            <HighlightedTextDisplay textDisplay={textDisplay} />
          </Typography>
        </Badge>
      <Divider/>
      </Grid>
      {
        /*
       <Grid item sm={3}>
       <Chip
         variant="outlined"
         color="primary"
         size="small"
         label={constraint.name}
       />
      </Grid>

       */
      }
    </Grid>
  );
}


export function getRenderOption(options: Option[], keyword: string){
    return (option: Option, { selected }: {selected: boolean}) => {
      // is_ambiguous is used to differentiate (in front-end) options sharing the same values but having different ids 
      const is_ambiguous = options.reduce(
        (acc, o) => acc || ((o.value === option.value) && (o.id !== option.id)), false
        );
      let text = (option.id !== undefined) && is_ambiguous ? option.value + " (" + option.id + ")" : option.value;
      const matches = match(text, keyword);
      let parts = parse(text, matches);
      return (
        <FilterOption {...option} textDisplay={parts} selected={selected} />
      );
    }
}

// This component is a wrapper of Material's UI Autocomplete, restricted to its more fundamental parameters.
// We use this wrapper for our more customized filters
export function AutocompleteOptions({
  keyword,
  setKeyword,
  options,
  setSelection,
  selection,
  label,
  placeholder,
  inputProps,
  onInputChange,
  renderInput,
  renderOption
}: {
  label: string;
  placeholder: string;
  keyword: string;
  setKeyword: (keyword: string) => void;
  options: Option[];
  selection: Option[];
  setSelection: (selection: Option[]) => void;
  inputProps?: object,
  onInputChange?: (reason: any, keyword: string) => void
  renderInput?: (params: AutocompleteRenderInputParams) => React.ReactNode,
  renderOption?: (option: Option, state:AutocompleteRenderInputParams)=>React.ReactNode
}) {


  return (
    <Autocomplete
      multiple
      value={selection}
      inputValue={keyword}
      onInputChange={onInputChange?onInputChange:(event, newKeyword) => {
        setKeyword(newKeyword)
      } }
      options={options}
      filterSelectedOptions
      noOptionsText="Aucun filtre trouvé"
      getOptionSelected={(a: Option, b: Option) =>
        a.value === b.value && a.constraint.api === b.constraint.api
      }
      onChange={(_, newValue: Option[]) => {
        setSelection(newValue);
      }}
      getOptionLabel={getOptionSynonym}
      renderTags={() => null}
      
      renderOption={renderOption?renderOption:getRenderOption(options, keyword)}
      
      renderInput={renderInput?renderInput:
        (params) => (
        <TextField {...params} label={label} placeholder={placeholder} />
      )}
      {...inputProps as any}

    />
  );
}

// This component enables to select fields (POSSIBLY SEVERAL VALUES PER FIELD) and to apply the filters to the global SIANCE context
function AddFiltersToContext({
  filtersForAutocomplete,
  validateAction,
  title,
}: {
  title?: string;
  filtersForAutocomplete: ConstraintType[];
  validateAction?: (action?: any) => void;
}) {
  const { filters: searchFilters, dispatch } = useSearchRequest();
  const [keyword, setKeyword] = React.useState<string>("");

  const delayedKeyword = useDebounce(keyword, 200);
  const options = useCombinedCompletions(
    filtersForAutocomplete,
    delayedKeyword
  );
  const selection = React.useMemo(
    () =>
      filtersForAutocomplete.flatMap((filter) =>
        searchFilters[filter.api].map((value) => ({
          constraint: filter,
          value: value,
          count: undefined,
        }))
      ),
    [searchFilters, filtersForAutocomplete]
  );

  return (
    <AutocompleteOptions
      options={options || []}
      keyword={keyword}
      setKeyword={setKeyword}
      setSelection={(newSelection) => {
        filtersForAutocomplete.forEach((filterName) =>
          dispatch({
            type: "ADD_CONSTRAINT",
            constraintElement: {
              constraint: filterName,
              values: newSelection
                .filter(
                  (v) =>
                    v.constraint.api === filterName.api &&
                    searchFilters[filterName.api].every((n) => n !== v.value)
                )
                .map((option) => option.value),
            },
          })
        );
        validateAction && validateAction(newSelection);
      }}
      selection={selection}
      label={title || "Cliquez ici pour ajouter des contraintes"}
      placeholder={filtersForAutocomplete.map((f) => f.name).join(", ")}
    />
  );
}


// This component enables to select fields (POSSIBLY SEVERAL VALUES PER FIELD) without applying the filters to the global SIANCE context
export function AddFiltersNoContext(
  {localValues, setLocalValues, filtersForAutocomplete, title} :
  {localValues: Option[], setLocalValues: (localValues: Option[])=>void, filtersForAutocomplete: ConstraintType[], title: string},
  ) {

    // localValues are the values of the local context, stored as strings
    const [keyword, setKeyword] = React.useState<string>("");
  
    const delayedKeyword = useDebounce(keyword, 200);
    const ignoreConstraint = true;
    const options = useCombinedCompletions(
      filtersForAutocomplete,
      delayedKeyword,
      ignoreConstraint
    );

    const selection =  React.useMemo(
      () => localValues,
      [localValues]
    );


    
    return (
      <AutocompleteOptions
        options={options || []}
        keyword={keyword}
        setKeyword={setKeyword}
        setSelection={(selection) => {setLocalValues(selection)}}
        selection={selection as Option[]}
        label={title || "Cliquez ici pour ajouter des contraintes"}
        placeholder={filtersForAutocomplete.map((f) => f.name).join(", ")}
        />
        
    );

  }
  

// This component enables to select fields (POSSIBLY SEVERAL VALUES PER FIELD) without applying the filters to the global SIANCE context
export function ReplaceFilterNoContext(
  {localValues, setLocalValues, filtersForAutocomplete, title} :
  {localValues: Option[], setLocalValues: (localValues: Option[])=>void, filtersForAutocomplete: ConstraintType[], title?: string},
  ) {

    // localValues are the values of the local context, stored as strings
    const [keyword, setKeyword] = React.useState<string>("");
  
    const delayedKeyword = useDebounce(keyword, 200);
    const ignoreConstraint = true;
    const options = useCombinedCompletions(
      filtersForAutocomplete,
      delayedKeyword,
      ignoreConstraint
    );

    const selection =  React.useMemo(
      () => localValues.slice(localValues.length,localValues.length), // slice to keep only the last asked filter
      [localValues]
    );

    const defaultLabel = filtersForAutocomplete.map((filter) => filter.name).join(" - ");
    
    return (
      <AutocompleteOptions
        options={options || []}
        keyword={keyword}
        setKeyword={setKeyword}
        setSelection={(selection) => {setLocalValues(selection)}}
        selection={selection as Option[]}
        label={title || "Cliquez ici pour changer les filtres"}
        placeholder={title || `Choisir un autre ${defaultLabel.toLowerCase()}`}
        />
        
    );

  }
  

// This component enables to select fields (ONLY ONE VALUE PER FIELD) and to apply the filters to the global SIANCE context
export function ReplaceFilterToContext({
  filters,
  title,
}: {
  title?: string;
  filters: ConstraintType[];
}) {
  // const filter = filters[0];
  const { filters: searchFilters, dispatch } = useSearchRequest();
  const [keyword, setKeyword] = React.useState<string>("");
  const delayedKeyword = useDebounce(keyword, 200);
  const options = useCombinedCompletions(filters, delayedKeyword);
  const selection = React.useMemo(
    () =>
      filters
        .flatMap((filter) =>
          searchFilters[filter.api].map((value) => ({
            constraint: filter,
            value: value,
            count: undefined,
          }))
        )
        .slice(0, 1),  // slice to keep only the last asked filter
    [searchFilters, filters]
  );


  const setSelection = function (newSelection: any[]) {
    filters.forEach((filter) => {
      dispatch({
        type: "SET_CONSTRAINTS",
        constraintElement: {
          constraint: filter,
          values: []
        }
      });
      dispatch({
        type: "SET_CONSTRAINTS",
        constraintElement: {
          constraint: filter,
          values: newSelection
          .filter(
            (v) => {
              let output = (v.constraint.api === filter.api && searchFilters[filter.api].every((n) => n !== v.value));
              return output
            }

          )
          .map((option) => option.value),
        }
      });
    })
  };

  const defaultLabel = filters.map((filter) => filter.name).join(" - ");

  return (
    <AutocompleteOptions
      options={options || []}
      keyword={keyword}
      setKeyword={setKeyword}
      setSelection={setSelection}
      selection={selection}
      label={
        selection && selection.length
          ? selection[selection.length - 1].value // selection can be an empty list or a singleton
          : defaultLabel
      }
      placeholder={title || `Choisir un autre ${defaultLabel.toLowerCase()}`}
    />
  );
}

export default AddFiltersToContext;
