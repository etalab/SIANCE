import React from "react";
import {
  Theme,
} from "../contexts/Search";
import {CombinedCompletionResult as Option} from "../hooks/UseCombinedCompletions";
import {AddFiltersNoContext} from "../components/FilterAutocomplete";


export default function SelectThemes({
    themes,
    setThemes
} : {
    themes:Option[],
    setThemes: (themes: Option[])=>void
}) {
  return (
    <AddFiltersNoContext 
      localValues={themes}
      setLocalValues={setThemes}
      filtersForAutocomplete={[Theme]}
      title="Visualiser des thèmes"
    />
  );
}