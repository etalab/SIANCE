// from stackoverflow
import React, { useEffect } from "react";
import PropTypes from "prop-types";
import Chip from "@material-ui/core/Chip";
import { makeStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import {AutocompleteRenderInputParams} from "@material-ui/lab/Autocomplete";

import useSearchRequest from "../contexts/Search";
import {
    ConstraintType,
} from "../contexts/Search"

import { useDebounce } from "../api/Api";
import {AutocompleteOptions, getRenderOption} from "./FilterAutocomplete";
import {
  CombinedCompletionResult as Option, useCombinedCompletion,
} from "../hooks/UseCombinedCompletions";

const useStyles = makeStyles(theme => ({
  chip: {
    margin: theme.spacing(0.5, 0.25)
  }
}));

export default function FiltersChip({ ...props }) {
  const classes = useStyles();
  const { selectedTags, constraint, placeholder, label } = props;
  const [inputValue, setInputValue] = React.useState("");
  const { filters, dispatch } = useSearchRequest();

  const [selectedItem, setSelectedItem] = React.useState<Option[]>([]);
  const selection = React.useMemo(
    () =>
        (filters[(constraint as ConstraintType).api] as string[]).map((value: string) => ({
          constraint: constraint,
          value: value,
          count: undefined,
        })
      ),
    [filters, constraint]
  );  // linking text entered in text bar with Option objects

  // populate selectedItem with parent tags (strings)
  useEffect(() => {
    setSelectedItem(selection);
  }, [selection]);
  // apply effect of selectedTags on tags
  useEffect(() => {
    selectedTags(selectedItem);
  }, [selectedItem, selectedTags]);

  const delayedKeyword = useDebounce(inputValue, 200);
  const options = useCombinedCompletion(
    constraint,
    delayedKeyword
  );

  const dispatchItems = (selectedItem: Option[]) => {
    dispatch({
      type: "SET_CONSTRAINTS",
      constraintElement: {
      constraint: constraint,
      values: selectedItem.map(option=>option.value),
      },
    })
  }

  const handleDelete = (item: string) => () => {
    const newSelectedItem = [...selectedItem];
    newSelectedItem.splice(newSelectedItem.map(option => option.value).indexOf(item as string), 1);
    setSelectedItem(newSelectedItem);
    dispatch({
        type: "DEL_CONSTRAINT",
        constraintElement: {
        constraint: constraint,
        values: [item],
        },
    })
  };


  return (
    <React.Fragment>
      <AutocompleteOptions
        options={(options || []) as unknown as Option[]}
        keyword={inputValue}
        placeholder={placeholder}
        setKeyword={(inputValue: string) => {
          setInputValue(inputValue)
        }}
        setSelection={(selectedItem: Option[]) => {
          setSelectedItem(selectedItem)
          dispatchItems(selectedItem)
        }}
        selection={selectedItem} // forget information
        label={label}
        renderOption={getRenderOption((options || []) as Option[], inputValue) as (option: Option, state:object)=>React.ReactNode}
        renderInput={(params: AutocompleteRenderInputParams)=>{
          return (
            <TextField {...params}
              style={{ margin: "10px" }}

              label={label}
              placeholder={placeholder}
              InputProps={{
                ref: params?.InputProps.ref,
                className: params?.InputProps.className,
                endAdornment: params?.InputProps.endAdornment,
                // at every moment, display only the last selected chip for this constraint
                startAdornment: selectedItem.slice(selectedItem.length-2,selectedItem.length).map((option: Option) => (
                  <Chip
                    key={option.value}
                    tabIndex={-1}
                    title={option.value}
                    label={(option.value.length <= 15 ? option.value: option.value.slice(0,15)+"...")}
                    size="small"
                    className={classes.chip}
                    onDelete={handleDelete(option.value)}
                  />
                ))
              }}
            />
          )
        }}
      />
    </React.Fragment>
  );
}
FiltersChip.defaultProps = {
  tags: []
};
FiltersChip.propTypes = {
  selectedTags: PropTypes.func.isRequired,
  tags: PropTypes.arrayOf(PropTypes.string)
};
