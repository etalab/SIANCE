import React from "react";
import {
  EquipmentsTrigrams,
} from "../contexts/Search";
import {CombinedCompletionResult as Option} from "../hooks/UseCombinedCompletions";
import {AddFiltersNoContext} from "../components/FilterAutocomplete";


export default function SelectSystem(
  {systems, setSystems}:
  {systems: Option[], setSystems: (systems: Option[])=>void},
){

  return (
    <AddFiltersNoContext 
      localValues={systems}
      setLocalValues={setSystems}
      filtersForAutocomplete={[EquipmentsTrigrams]}
      title="Visualiser des systèmes REP"
    />
  );
}