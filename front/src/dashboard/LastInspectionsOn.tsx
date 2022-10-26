import React from "react";
import {
  Card,
  CardHeader,
  CardContent,
  CircularProgress,
  makeStyles,
  Menu,
  MenuItem,
  List,
  ListItem,
} from "@material-ui/core";

import LetterSummary from "../searchPage/LetterSummary";

import useSearchRequest, {
  ConstraintType,
  InterlocutorName,
  Topics,
  SiteName,
  Theme,
} from "../contexts/Search";

import { useLastResultsMatching } from "../hooks/UseSearchResponse";

const useHorizontalScrollStyle = makeStyles((theme) => ({
  root: {
    display: "grid",
    gridAutoFlow: "column",
    [theme.breakpoints.only("xl")]: {
      gridAutoColumns: "30%",
    },
    [theme.breakpoints.only("lg")]: {
      gridAutoColumns: "50%",
    },
    [theme.breakpoints.only("md")]: {
      gridAutoColumns: "60%",
    },
    [theme.breakpoints.only("sm")]: {
      gridAutoColumns: "90%",
    },
    [theme.breakpoints.only("xs")]: {
      gridAutoColumns: "110%",
    },
    gridGap: theme.spacing(1),
    overflowX: "scroll",
    overflowY: "hidden",
    paddingBottom: theme.spacing(1),
  },
}));

function HorizontalScrollGrid({ children }: { children: React.ReactNode }) {
  const styles = useHorizontalScrollStyle();
  return <div className={styles.root}>{children}</div>;
}

const selectableFilters = [InterlocutorName, Theme, Topics, SiteName];

export function SelectableLastInspection() {
  const [currentFilter, setCurrentFilter] = React.useState<number>(0);
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleClickListItem = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuItemClick = (
    _: React.MouseEvent<HTMLElement>,
    index: number
  ) => {
    setCurrentFilter(
      Math.max(0, Math.min(selectableFilters.length - 1, index))
    );
    setAnchorEl(null);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  return (
    <>
      <LastInspectionsOn
        title={
          <List component="span" aria-label="sélection de sous catégorie">
            <ListItem button aria-haspopup="true" onClick={handleClickListItem}>
              Dernières lettres de suite selon le filtre{" "}
              {selectableFilters[currentFilter].name}
            </ListItem>
          </List>
        }
        filter={selectableFilters[currentFilter]}
      />
      <Menu
        anchorEl={anchorEl}
        keepMounted
        open={Boolean(anchorEl)}
        onClose={handleClose}
      >
        {selectableFilters.map((option, index) => (
          <MenuItem
            key={option.api}
            selected={index === currentFilter}
            onClick={(event) => handleMenuItemClick(event, index)}
          >
            Dernières lettres de suite selon le filtre {option.name}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}

function LastInspectionsOn({
  title,
  filter,
}: {
  title: React.ReactNode;
  filter: ConstraintType;
}) {
  const { filters } = useSearchRequest();
  const { data } = useLastResultsMatching(filter, filters[filter.api]);
  return (
    <Card variant="outlined">
      <CardHeader title={title} />
      <CardContent>
        <HorizontalScrollGrid>
          {data ? (
            data.hits.map((document) => (
              <LetterSummary
                key={document.doc_id}
                isCorrect={true}
                highlighted={[]}
                docid={document.doc_id}
                letter={document._source}
              />
            ))
          ) : (
            <CircularProgress />
          )}
        </HorizontalScrollGrid>
      </CardContent>
    </Card>
  );
}

export default LastInspectionsOn;
