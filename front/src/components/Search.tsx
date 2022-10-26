import React from "react";

import {
  Grid,
  IconButton,
  ButtonGroup,
  Typography,
  makeStyles,
  CircularProgress,
  Paper,
  InputBase,
  Divider,
  Badge,
} from "@material-ui/core";

import Autocomplete, {
  AutocompleteRenderInputParams,
} from "@material-ui/lab/Autocomplete";

import { parse, match, HighlightedTextDisplay } from "../lib/StringMatch";

import DeleteIcon from "@material-ui/icons/Delete";

import useStickyResult from "../hooks/Sticky";

import useSearchRequest from "../contexts/Search";

import useNavigation from "../navigation/Utils";
import { Rechercher, Visualiser, Observer, Accueil } from "../Pages";

import { useThrottle } from "../hooks/Time";

import SectorsIconBar from "../components/SectorsIconBar";

import useOnTheFlyAutocomplete from "../hooks/UseOnTheFlyAutocomplete";
import { useLettersSuggestResponse } from "../hooks/UseSuggestResponse";

type TextAutoCompleteProps = {
  showSearchIcon?: boolean;
  options: string[];
  setSelected: (selection: string) => void;
  isValidating: boolean;
  label?: string;
  placeholder?: string;
  freeSolo?: boolean;
  onValidated?: (selection: string) => void;
  inputValue?: string;
};

const useStyles = makeStyles((theme) => ({
  root: {
    padding: "2px 4px",
    display: "flex",
    alignItems: "center",
  },
  input: {
    marginLeft: theme.spacing(1),
    flex: 1,
  },
  iconButton: {
    padding: 10,
  },
  divider: {
    height: 28,
    margin: 4,
  },
}));

function MainSearchField({
  isValidating,
  ...params
}: { isValidating: boolean } & AutocompleteRenderInputParams) {
  const classes = useStyles();

  const { filters } = useSearchRequest();

  let filtersSummary = Object.entries(filters).map(
    ([k, v]) => (v.length > 0) ? v : undefined
  ).filter(f=>f).join("\n - ")
  filtersSummary = filtersSummary.length > 0 ? "Réinitialiser la recherche : \n - " + filtersSummary : ""
    

  const filtersCount = Object.entries(filters)
    .map(([_, b]) => b.length)
    .reduce((a, b) => a + b, 0);

  return (
    <>
      <Paper className={classes.root}>
        <ButtonGroup
          className={classes.iconButton}
          color="primary"
          aria-label="sectors-smart-buttons"
        >
          <SectorsIconBar />
        </ButtonGroup>
        <Divider className={classes.divider} orientation="vertical" />
        <InputBase
          ref={params.InputProps.ref}
          autoFocus
          className={classes.input}
          placeholder="Mots-clefs, numéros d'inspection..."
          inputProps={{ ...params.inputProps, "aria-label": "main-search-bar" }}
        />

        <button
          style={{ display: "none" }}
          type="submit"
          name="textEnter"
        ></button>
        <IconButton
          type="submit"
          className={classes.iconButton}
          aria-label="search"
          name={Rechercher.name}
          title={Rechercher.name}
        >
          {isValidating ? (
            <CircularProgress color="inherit" size={20} />
          ) : (
            Rechercher.icon
          )}
        </IconButton>
        <Divider className={classes.divider} orientation="vertical" />
        <IconButton
          color="primary"
          className={classes.iconButton}
          aria-label="directions"
          title={Visualiser.name}
          type="submit"
          name={Visualiser.name}
        >
          {Visualiser.icon}
        </IconButton>
        <Divider className={classes.divider} orientation="vertical" />
        <IconButton
          color={filtersCount > 0 ? "secondary" : undefined}
          className={classes.iconButton}
          aria-label="reset-search"
          title={filtersSummary}
          name="reset-search"
          type="submit"
        >
          <Badge badgeContent={filtersCount} max={9}>
            <DeleteIcon fontSize="small" />
          </Badge>
        </IconButton>
      </Paper>
    </>
  );
}

export function TextAutocomplete({
  options,
  onValidated,
  setSelected,
  isValidating,
  freeSolo,
  inputValue,
}: TextAutoCompleteProps) {
  return (
    <Autocomplete
      freeSolo={freeSolo || false}
      loadingText="Calcul des suggestions..."
      loading={isValidating}
      options={options}
      inputValue={inputValue}
      // clearOnBlur
      // autoSelect
      onInputChange={(_, v, r) => {
        ((r === "reset" && v !== null && v !== "") ||
          (r !== "reset" && v !== null)) &&
          setSelected(v);
      }}
      onChange={(_, v, _a) => {
        v !== null && onValidated && onValidated(v);
      }}
      renderOption={(option, { inputValue }) => {
        const matches = match(option, inputValue);
        const parts = parse(option, matches);

        return (
          <div>
            <HighlightedTextDisplay textDisplay={parts} />
          </div>
        );
      }}
      renderInput={(params) => (
        <MainSearchField isValidating={isValidating} {...params} />
      )}
    />
  );
}

export type SearchBarProps = {
  showSearchIcon?: boolean;
};
export default function SearchBar({ showSearchIcon }: SearchBarProps) {
  const { goToPage, currentPage } = useNavigation();

  const { dispatch, sentence } = useSearchRequest();

  const [typingText, setTypingText] = React.useState<string>(sentence);

  const typedText = useThrottle(typingText, 1500);

  React.useEffect(() => {
    setTypingText(sentence);
  }, [sentence]);

  const {
    data: rawCompletions,
    isValidating: completionsValidating,
  } = useOnTheFlyAutocomplete(typedText);
  const completions = useStickyResult(rawCompletions);

  const { data: rawSuggestion } = useLettersSuggestResponse();

  const suggestions = useStickyResult(rawSuggestion);

  function build_did_you_mean_text(s: string, real: string) {
    return (
      <>
        Vouliez vous dire:{" "}
        <a
          href="#localhost"
          onClick={(e) => {
            e.preventDefault();
            setTypingText(real);
            dispatch({ type: "SET_SENTENCE", value: real });
          }}
        >
          {s.split("###").map((e, i) =>
            i % 2 === 1 ? (
              <span key={e} style={{ fontWeight: 500 }}>
                {e}
              </span>
            ) : (
              e
            )
          )}
        </a>
      </>
    );
  }

  return (
    <Grid container alignItems="center" justify="space-between">
      <Grid item xs={12} sm={12}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const howWasItSumitted = (e.nativeEvent as any)?.submitter?.name;
            dispatch({
              type: "SET_SENTENCE",
              value: typingText,
            });
            console.log(howWasItSumitted);
            switch (howWasItSumitted) {
              case Visualiser.name:
                if (currentPage !== Visualiser) {
                  goToPage(Visualiser, undefined);
                }
                break;
              case Rechercher.name:
                if (currentPage !== Rechercher) {
                  goToPage(Rechercher, undefined);
                }
                break;
              case "reset-search":
                dispatch({ type: "RESET_SEARCH" });
                if (currentPage === Observer) {
                  goToPage(Rechercher, undefined);
                }
                break;
              default:
                if (currentPage === Observer || currentPage === Accueil) {
                  goToPage(Rechercher, undefined);
                }
            }
          }}
          autoComplete="off"
        >
          <TextAutocomplete
            inputValue={typingText}
            options={completions || []}
            onValidated={(v) => {
              setTypingText(v);
              dispatch({ type: "SET_SENTENCE", value: v });
            }}
            setSelected={(s) => setTypingText(s)}
            isValidating={completionsValidating}
            freeSolo
            showSearchIcon={showSearchIcon}
          />
        </form>
      </Grid>
      <Grid item>
        <Typography>
          {suggestions && suggestions["dym"] && suggestions["dym"].length > 0
            ? build_did_you_mean_text(
                suggestions["dym"][0]?.highlighted,
                suggestions["dym"][0]?.text
              )
            : null}
        </Typography>
      </Grid>
    </Grid>
  );
}
