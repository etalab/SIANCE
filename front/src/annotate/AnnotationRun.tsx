import React from "react";

import {
  Divider,
  Paper,
  Grid,
  List,
  ListItem,
  ListItemText,
  Typography,
  Button,
  Box,
  LinearProgress,
  Menu,
  MenuItem,
} from "@material-ui/core";

import useOntology from "../hooks/UseOntology";
import { Annotation } from "../hooks/UseAnnotations";

export type AnsweredAnnotation = Annotation & {
  userResponse: boolean | undefined;
};

type AnnotationAction =
  | {
      type: "ANSWER";
      option: number;
      userResponse: boolean | undefined;
    }
  | {
      type: "CHANGE_SUBCATEGORY";
      option: number;
      newTopics: {category: string, subcategory: string, id_label: number};
    }
  | {
      type: "INCR";
    }
  | {
      type: "DECR";
    };

type AnnotationRunState = {
  annotations: AnsweredAnnotation[];
  step: number;
};

function reduceAnnotation(
  oldState: AnnotationRunState,
  action: AnnotationAction
): AnnotationRunState {
  switch (action.type) {
    case "ANSWER":
      return {
        step: Math.min(oldState.annotations.length - 1, oldState.step + 1),
        annotations: oldState.annotations.map((answ, index) =>
          index === action.option
            ? { ...answ, userResponse: action.userResponse }
            : answ
        ),
      };
    case "CHANGE_SUBCATEGORY":
      return {
        step: Math.min(oldState.annotations.length - 1, oldState.step),
        annotations: [
          ...oldState.annotations.slice(0, action.option),
          //         { ...oldState.annotations[action.option], userResponse: false },
          {
            ...oldState.annotations[action.option],
            userResponse: true,
            subcategory: action.newTopics.subcategory,
            category: action.newTopics.category,
            id_label: action.newTopics.id_label,

          },
          ...oldState.annotations.slice(action.option + 1),
        ],
      };
    case "INCR":
      return {
        ...oldState,
        step: Math.min(oldState.annotations.length - 1, oldState.step + 1),
      };
    case "DECR":
      return { ...oldState, step: Math.max(0, oldState.step - 1) };
  }
}

const useAnnotationRun = (initialArgs: Annotation[]) => {
  return React.useReducer(reduceAnnotation, initialArgs, (values) => ({
    step: 0,
    annotations: values.map((a) => ({ userResponse: undefined, ...a })),
  }));
};

function SubcategoryMenu({
  topic,
  onChange,
}: {
  topic: {category: string, subcategory: string; id_label: number};
  onChange: (topic: {category: string, subcategory: string; id_label: number}) => void;
}) {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const { data: ontology } = useOntology();
  const options = ontology
    ? ontology
        .filter((node) => node.category === topic.category)
        .flatMap((node) => node.subcategories)
    : [topic];

  const handleClickListItem = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuItemClick = (
    _: React.MouseEvent<HTMLElement>,
    index: number
  ) => {
    onChange(options[index]);
    setAnchorEl(null);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  return (
    <div title="Cliquer ici pour changer la catégorie">
      <List component="nav" aria-label="sélection de sous catégorie">
        <ListItem
          button
          aria-haspopup="true"
          aria-controls="lock-menu"
          aria-label={topic.category}
          onClick={handleClickListItem}
        >
          <ListItemText
            primary={topic.category}
            secondary={topic.subcategory}
          />
        </ListItem>
      </List>
      <Menu
        id="lock-menu"
        anchorEl={anchorEl}
        keepMounted
        open={Boolean(anchorEl)}
        onClose={handleClose}
      >
        {options.map((option, index) => (
          <MenuItem
            key={option.id_label}
            selected={option.id_label === topic.id_label}
            onClick={(event) => handleMenuItemClick(event, index)}
          >
            {option.subcategory}
          </MenuItem>
        ))}
      </Menu>
    </div>
  );
}

function AnswerYesNoAnnotation({
  annotation,
  sayYes,
  sayNo,
  reset,
  correct,
  name,
}: {
  annotation: AnsweredAnnotation;
  sayYes: () => void;
  reset: () => void;
  sayNo: () => void;
  correct: (x: {category: string, subcategory: string; id_label: number}) => void;
  name: string;
}) {
  const value = annotation.userResponse;
  const topic = {
    category: annotation.category,
    subcategory: annotation.subcategory,
    id_label:  annotation.id_label
  }
  const content = annotation.sentence;

  return (
    <Grid container justify="center" style={{ textAlign: "center" }}>
      <Grid item sm={12}>
        <Typography variant="h4" color="primary">
          Proposition {name}
        </Typography>
      </Grid>
      <Grid item sm={12} lg={6}>
        <Typography variant="h6" gutterBottom>
            {annotation.letter_name}
        </Typography>
        <Typography>
          <Box m={1}>
            <span title={content.length>300? content: ""}>
              {
                content.length > 300 ?
                content.slice(0,300)+"..." : content
              }
            </span>
          </Box>
        </Typography>
      </Grid>
      <Grid item sm={12} lg={6}>
        <Typography variant="h6" gutterBottom>
          Catégorie proposée
        </Typography>
        <span className="italic">Cliquer sur la catégorie pour la modifier</span>
        <SubcategoryMenu topic={topic} onChange={correct} />
      </Grid>
      <Grid item sm={12}>
        <Divider />
      </Grid>
      <Grid item sm={6}>
        <Button
          onClick={sayYes}
          color="primary"
          style={{ width: "100%", height: "5em" }}
          variant={value === true ? "contained" : undefined}
        >
          Valider
        </Button>
      </Grid>
      <Grid item sm={6}>
        <Button
          onClick={sayNo}
          color="secondary"
          style={{ width: "100%", height: "5em" }}
          variant={(value === false) || (value === undefined) ? "contained" : undefined}
        >
          Aucune de ces catégories
        </Button>
      </Grid>
    </Grid>
  );
}

function AnnotationRun({
  annotations,
  validate,
}: {
  annotations: Annotation[];
  validate: (annotations: AnsweredAnnotation[]) => void;
}) {
  const [currentState, dispatch] = useAnnotationRun(annotations);
  const { step: currentStep, annotations: currentAnnotations } = currentState;
  const runsize = currentAnnotations.length;
  const isFinished = currentStep === runsize - 1;

  return (
    <Paper>
      <Grid container spacing={0} alignItems="center">
        <Grid item sm={6}>
          <Box ml={2} mt={1} mb={1}>
            <Typography variant="h5">Annotations</Typography>
          </Box>
        </Grid>
        <Grid item sm={3}>
          <Button
            style={{ height: "5em" }}
            onClick={() => dispatch({ type: "DECR" })}
          >
            Précédent
          </Button>
        </Grid>
        <Grid item sm={3}>
          {isFinished ? (
            <Button
              variant="contained"
              color="primary"
              style={{ height: "5em" }}
              onClick={() => validate(currentAnnotations)}
            >
              Confirmer
            </Button>
          ) : (
            <Button
              style={{ height: "5em" }}
              onClick={() => dispatch({ type: "INCR" })}
            >
              Suivant
            </Button>
          )}
        </Grid>
        <Grid item sm={12}>
          <LinearProgress
            variant="determinate"
            value={((currentStep + 1) / runsize) * 100}
          />
        </Grid>
        <Grid item sm={12}>
          <AnswerYesNoAnnotation
            sayYes={() => {
              dispatch({
                type: "ANSWER",
                option: currentStep,
                userResponse: true,
              });
            }}
            sayNo={() => {
              dispatch({
                type: "ANSWER",
                option: currentStep,
                userResponse: false,
              });
            }}
            reset={() =>
              dispatch({
                type: "ANSWER",
                option: currentStep,
                userResponse: undefined,
              })
            }
            correct={(x: {category: string, subcategory: string; id_label: number}) =>
              dispatch({
                type: "CHANGE_SUBCATEGORY",
                option: currentStep,
                newTopics: x,
              })
            }
            name={`${currentStep + 1}/${runsize}`}
            annotation={currentAnnotations[currentStep]}
          />
        </Grid>
      </Grid>
    </Paper>
  );
}

export default AnnotationRun;
