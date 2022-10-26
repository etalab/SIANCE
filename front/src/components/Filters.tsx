import React from "react";

import {
  Button,
  ButtonGroup,
  Badge,
  Chip,
  Grid,
  Divider,
  Typography,
  TextField,
  Card,
  Box,
  Dialog,
  DialogTitle,
  DialogActions,
  DialogContent,
} from "@material-ui/core";
import AddIcon from "@material-ui/icons/Add";

import {
  constraintList,
  ConstraintType,
  SearchFiltersT,
} from "../contexts/Search";
import useInspectDisplay, {
  useInspectDispatchDisplay,
} from "../searchPage/contexts/Displays";

import CategorySelector from "../components/CategorySelector";

import useSearchRequest from "../contexts/Search";

import FieldSelectionDialog from "../components/FieldSelectionDialog";
import useStickyResult from "../hooks/Sticky";

import {
  useLettersSuggestResponse,
  SuggestLettersResponse,
} from "../hooks/UseSuggestResponse";

import FiltersChip from "./FiltersChip"

type Option = {
  value: string;
  count?: number;
};

type GenericFilterSelectionProps = {
  constraint: ConstraintType;
  suggestions: Option[];
  selection: string[];
};

function GenericFilterSelection({
  constraint,
  suggestions,
  selection,
}: GenericFilterSelectionProps) {
  const dispatch = useInspectDispatchDisplay();
  const { showFieldControls } = useInspectDisplay();

  return (
    <React.Fragment key={constraint.api}>
      <FieldSelectionDialog
        key={`${constraint.api}-dialog`}
        constraint={constraint}
        open={showFieldControls === constraint.api}
        onClose={() => dispatch({ type: "QUIT_SELECT_FIELD" })}
      />
      <Divider />
      <Grid container spacing={1} justify="flex-start" style={{ padding: 10 }}>
        <DisplayFilters constraint={constraint} values={selection} />
        <DisplaySuggestions
          constraint={constraint}
          values={usefullSuggestions<string, Option>(
            selection,
            suggestions,
            (x) => x.value
          )}
        />
        <Grid item>
          <Chip
            icon={<AddIcon />}
            key={constraint.api}
            label="Ajouter"
            onClick={() =>
              dispatch({
                type: "SELECT_FIELD",
                constraintName: constraint.api,
              })
            }
          />
        </Grid>
      </Grid>
    </React.Fragment>
  );
}

const modeList = [
  "research",
  "is_rep",
  "is_ludd",
  "is_npx",
  "is_transverse",
] as const;
//const modeNames = ["Tout", "REP", "LUDD", "NPX", "Transverse"] as const;
function CategoryFilterSelection({
  constraint,
  subcategoriesCount,
}: {
  subcategoriesCount: Map<string, number>;
} & GenericFilterSelectionProps) {
  const { filters, dispatch: dispatchR } = useSearchRequest();

  const [mode] = React.useState<0 | 1 | 2 | 3 | 4>(0);

  const add = React.useCallback(
    (values) =>
      dispatchR({
        type: "ADD_CONSTRAINT",
        constraintElement: {
          constraint: constraint,
          values: values,
        },
      }),
    [constraint, dispatchR]
  );

  const del = React.useCallback(
    (values) =>
      dispatchR({
        type: "DEL_CONSTRAINT",
        constraintElement: {
          constraint: constraint,
          values: values,
        },
      }),
    [constraint, dispatchR]
  );

  const cats = React.useMemo(() => new Set(filters[constraint.api]), [
    filters,
    constraint,
  ]);

  return (
    <Card variant="outlined" key={constraint.api}>
      <Box p={1}>
        <CategorySelector
          mode={modeList[mode]}
          addItem={add}
          deleteItem={del}
          selectedSubcategoryCodes={cats}
          subcategoriesCount={subcategoriesCount}
        />
      </Box>
    </Card>
  );
}

type DisplayFiltersProps<T> = {
  constraint: ConstraintType;
  values: T[];
};

function ChipFilter({ constraint, value }: {constraint: ConstraintType; value: (string | number)}) {
  const { dispatch } = useSearchRequest();
  return (
    <Chip
    color="primary"
    label={`${value}`}
    title={`${value}`}
    style={{ maxWidth: "100%" }}
    onDelete={() =>
      dispatch({
        type: "DEL_CONSTRAINT",
        constraintElement: {
          constraint: constraint,
          values: [value],
        },
      })
    }
  />
  )
}

function DisplayFilters({ constraint, values }: DisplayFiltersProps<string>) {
  // display a bunch of chips: one chip per selected filter
  return (
    <React.Fragment>
      {values.map((item: string | number) => (
        <Grid item key={item} style={{ maxWidth: "100%" }}>
          <ChipFilter
            constraint={constraint}
            value={item}
          />
        </Grid>
      ))}
    </React.Fragment>
  );
}

export function usefullSuggestions<T, U>(
  constraints: T[],
  suggestions: U[],
  acc: (v: U) => T
): U[] {
  const removable = new Set(constraints);
  return suggestions.filter((x) => !removable.has(acc(x)));
}

export function DisplaySuggestions({
  constraint,
  values,
}: DisplayFiltersProps<Option>) {
  const { dispatch } = useSearchRequest();
  return (
    <React.Fragment>
      {values.slice(0, 2).map(({ value: item, count }) => (
        <Grid item key={item} style={{ maxWidth: "100%" }}>
          <Chip
            variant="outlined"
            icon={<AddIcon />}
            label={
              <Badge
                badgeContent={count}
                max={100}
                style={{
                  maxWidth: "100%",
                  marginTop: "8px",
                  marginBottom: "8px",
                  marginRight: "15px",
                }}
              >
                <Typography noWrap component="span">
                  {item}
                </Typography>
              </Badge>
            }
            style={{ maxWidth: "100%" }}
            onClick={() =>
              dispatch({
                type: "ADD_CONSTRAINT",
                constraintElement: {
                  constraint: constraint,
                  values: [item],
                },
              })
            }
          />
        </Grid>
      ))}
    </React.Fragment>
  );
}


function ConstraintTab({
  constraints,
  filters,
  showSuggestions,
  suggestions,
}: {
  constraints: ConstraintType[];
  filters: SearchFiltersT<string[]>;
  suggestions?: SuggestLettersResponse;
  showSuggestions: boolean;
}) {
  return (
    <>
      {constraints
        .filter(
          (v) =>
            !(
              filters.sectors.length > 0 &&
              filters.sectors.every((v) => v !== "REP") &&
              v.api === "equipments_trigrams"
            )
        )
        .map((c) => (
          <React.Fragment key={c.api}>
            {c.api === "topics" ? (
              <Grid item sm={12}>
                <CategoryFilterSelection
                  constraint={c}
                  suggestions={
                    (showSuggestions && suggestions && suggestions[c.api]) || []
                  }
                  selection={filters[c.api]}
                  subcategoriesCount={
                    new Map(
                      suggestions?.topics?.map((k) => [k.value, k.count || 0])
                    )
                  }
                />
              </Grid>
            ) : (
              <Grid item sm={12} md={6}>
                <GenericFilterSelection
                  constraint={c}
                  suggestions={
                    (showSuggestions && suggestions && suggestions[c.api]) || []
                  }
                  selection={filters[c.api]}
                />
              </Grid>
            )}
          </React.Fragment>
        ))}
    </>
  );
}

function DialogFilter({
  title,
  open,
  constraints,
  handleClose,
  filters,
  suggestions,
  showSuggestions,
} :
{
  title: string;
  open: boolean;
  constraints: ConstraintType[];
  handleClose: () => void;
  filters: SearchFiltersT<string[]>;
  suggestions?: SuggestLettersResponse;
  showSuggestions: boolean;
}) {
  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
    <DialogTitle>{title}</DialogTitle>
    <DialogContent>
      <Grid container spacing={1}>
        <ConstraintTab
          constraints={constraints}
          filters={filters}
          suggestions={suggestions}
          showSuggestions={showSuggestions}
        />
      </Grid>
    </DialogContent>
    <DialogActions>
      <Button onClick={handleClose}>OK</Button>
    </DialogActions>
  </Dialog>
  )
}

export default function NewFiltersPannel() {
  // the pannel with filters shared by page Search and Dashboard

  const { sentence, filters } = useSearchRequest();

  const { data } = useLettersSuggestResponse();

  const suggestions = useStickyResult(data ? data : undefined);
  const showSuggestions = constraintList.some(
    (c) => (sentence && true) || filters[c.api].length
  );

  // const [value, setValue] = React.useState<0 | 1 | 2>(0);
  const [visibleWindow, setVisibleWindow] = React.useState<string>("")
 // const [open, setOpen] = React.useState<boolean>(false);
  const handleClose = () => setVisibleWindow("");
  const handleOpen = (filterName: string) => {
    return () => setVisibleWindow(filterName);
  }
  /*
    <DisplayFilters constraint={constraint} values={filters[constraint.api]} />
    <DisplaySuggestions
      constraint={constraint}
      values={usefullSuggestions<string, Option>(
        filters[constraint.api],
        (showSuggestions && suggestions && suggestions[constraint.api]) || [],
        (x) => x.value
      )}
    />
*/
  //const [keywords, setKeywords] = React.useState<string[]>(new Array<string>(constraintList.length));

  const chooseColor = (constraint: ConstraintType):("primary"|"secondary") => {
    // if at least there is one value for this constraint, return the secondary color
    if (filters[constraint.api].length > 0){
      return "secondary"
    } else {
      return "primary"
    }
  }

  return (
    <Grid container spacing={1} direction="column">
      <ButtonGroup
        orientation="vertical"
        aria-label="vertical contained button group"

        >
        {
          constraintList.map((constraint, k) =>
            {
              return(
                <Grid item
                  style={{ margin: 2 }}
                >
                  { k < constraintList.length ? <Divider />: undefined}
                  <DialogFilter
                        title={constraint.name}
                        open={visibleWindow === constraint.name}
                        constraints={constraintList.slice(k,k+1)}
                        handleClose={handleClose}
                        filters={filters}
                        suggestions={suggestions}
                        showSuggestions={showSuggestions}
                      />
                  <Grid container xs={12} direction="row">
                    <Grid item xs={3} md={3}
                      style={{ flexDirection: "column" }}
                    >
                      <Button
                        variant="contained"
                        color={chooseColor(constraint)}
                        title={filters[constraint.api].join(",")}
                        value={constraint.name}
                        style={{height: "90%", margin: "5px"}}
                        onClick={handleOpen(constraint.name)}
                        fullWidth={true}
                        >{constraint.name.slice(0,18)}
                        
                      </Button>

                    </Grid>
                    <Grid item xs={9} md={9}>
                     <FiltersChip
                      selectedTags={()=>{}}
                      fullWidth
                      style={{ margin: "10px" }}
                      variant="outlined"
                      id="tags"
                      name={constraint.name}
                      placeholder={filters[constraint.api].length >= 4 ?
                         "ou "+ (filters[constraint.api].length -2) + " autres" :
                         (filters[constraint.api].length === 3 ? "ou 1 autre" :
                          (filters[constraint.api].length >= 1 ? "":
                          "Ajouter "+constraint.name.toLowerCase()
                         ))
                      }
                      constraint={constraint}
                      label={constraint.name}
                      renderInput={(params: any) => (
                        <TextField {...params} label={constraint.name} />
                      )}
                      />
                    </Grid>
                  </Grid>
                </Grid>
              )
            }
          )
        }
      </ButtonGroup>
    </Grid>
  )
}

