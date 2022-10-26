import React, { FunctionComponent } from "react";
import Container from "@material-ui/core/Container";

import { green } from "@material-ui/core/colors";
import HelpOutlineIcon from "@material-ui/icons/HelpOutline";
import ContactMailIcon from "@material-ui/icons/ContactMail";
import AssignmentIcon from "@material-ui/icons/Assignment";
import ContactSupportIcon from "@material-ui/icons/ContactSupport";
import CategoryIcon from "@material-ui/icons/Category";
import DirectionsIcon from "@material-ui/icons/Directions";

import Skeleton from "@material-ui/lab/Skeleton";

import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import Grid from "@material-ui/core/Grid";
import Autocomplete from "@material-ui/lab/Autocomplete";

import {
  makeStyles,
  List,
  Avatar,
  Box,
  ListItem,
  ListItemAvatar,
  TextField,
  ListItemText,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  ButtonBase,
  Stepper,
  Step,
  StepButton,
} from "@material-ui/core";

import Contact from "../contact/Contact";
import Pages from "../Pages";
import HelpDialog from "../searchPage/HelpDialog";

import useOntology, {
  OntologyItem,
  OntologySubcategory,
} from "../hooks/UseOntology";
import { useUserConfig } from "../authentication/Utils";

import conf from "../config.json";

const useStyles = makeStyles((theme) => ({
  activeStepButton: {
    color: theme.palette.primary.main,
  },
  button: {
    margin: theme.spacing(0, 1, 0, 1),
  },
  homeContainer: {
    padding: theme.spacing(2),
  },
}));

const contacts = [
  {
    name: "Développeurs et support technique",
    email: "contact-siance@asn.fr",
    location: "Bureau 4030 / MSC",
    description:
      "Personne à contacter en cas de problème technique, suggestions ou idées pour le développement de siance.",
    picture: "",
    status: "",
  },
];

type DisplayAndSelectListProps<T> = {
  items: T[];
  setSelection: React.Dispatch<React.SetStateAction<T | undefined>>;
  selection: T | undefined;
  display: (value: T) => string;
};

const useAutocompleteStyle = makeStyles((theme) => ({
  root: {
    gridRow: 1,
  },
  paper: {
    boxShadow: "none",
    margin: 0,
    color: "#586069",
    fontSize: 13,
  },
  option: {
    minHeight: "auto",
    alignItems: "flex-start",
    padding: 8,
    '&[aria-selected="true"]': {
      backgroundColor: "transparent",
    },
    '&[data-focus="true"]': {
      backgroundColor: theme.palette.action.hover,
    },
  },
  selected: {
    textDecoration: "underline",
  },
  popperDisablePortal: {
    position: "static",
    width: undefined,
    gridRow: 2,
    zIndex: 0,

    "& .MuiAutocomplete-listbox": {
      maxHeight: "30em",
      height: "30em",
      minHeight: "30em",
    },
  },
}));

function DisplayAndSelectList<T>({
  items,
  setSelection,
  selection,
  display,
}: DisplayAndSelectListProps<T>) {
  const classes = useAutocompleteStyle();
  return (
    <div style={{ display: "grid" }}>
      <Autocomplete
        open
        className={classes.root}
        classes={{
          paper: classes.paper,
          option: classes.option,
          popperDisablePortal: classes.popperDisablePortal,
        }}
        value={selection}
        options={items}
        onChange={(_, newValue) => newValue && setSelection(newValue)}
        disableCloseOnSelect
        disablePortal
        getOptionLabel={display}
        renderInput={(params) => <TextField {...params} />}
        renderOption={(option, { selected }) => {
          return (
            <div className={selected ? classes.selected : undefined}>
              {display(option)}
            </div>
          );
        }}
      />
      <Divider />
    </div>
  );
}

function DisplayCategories() {
  const { data, error, isValidating } = useOntology();
  const [currentCat, setCurrentCat] = React.useState<OntologyItem>();
  const [currentSCat, setCurrentSCat] = React.useState<OntologySubcategory>();

  return (
    <Box m={2} p={2}>
      <Grid container justify="space-around" spacing={2}>
        <Grid item xs={12} sm={6}>
          <Typography variant="h5">Catégories</Typography>
          {isValidating || error || !data ? (
            <>
              <ListItem>
                <Skeleton />
              </ListItem>
              <ListItem>
                <Skeleton />
              </ListItem>
            </>
          ) : (
            <DisplayAndSelectList
              items={data}
              setSelection={setCurrentCat}
              selection={currentCat}
              display={(c) => c.category}
            />
          )}
        </Grid>
        <Grid item xs={12} sm={6}>
          <Typography variant="h5" noWrap>
            Sous-catégories
            {currentCat ? ` de ${currentCat.category}` : null}
          </Typography>
          {isValidating || error || !data || !currentCat ? (
            <>
              <Skeleton height="3em" />
              <Skeleton height="3em" />
            </>
          ) : (
            <DisplayAndSelectList
              items={currentCat.subcategories}
              setSelection={setCurrentSCat}
              selection={currentSCat}
              display={(subcat) => subcat.subcategory}
            />
          )}
        </Grid>
      </Grid>
    </Box>
  );
}

type QuestionItemProps = {
  question: string;
};
const QuestionItem: FunctionComponent<QuestionItemProps> = ({
  children,
  question,
}) => {
  return (
    <ListItem>
      <ListItemAvatar>
        <Avatar style={{ background: green[500] }}>
          <HelpOutlineIcon />
        </Avatar>
      </ListItemAvatar>
      <ListItemText primary={question} secondary={children} />
    </ListItem>
  );
};

function FAQ() {
  return (
    <List>
      <QuestionItem question="Quelles sont les dernières actualités de SIANCE ?">
        Les dernières actualités de SIANCE sont consultables sur{" "}
        <a href="https://intranet-oasis.asn.i2/jcms/prod_107184/siance">
          OASIS
        </a>
        . Aujourd'hui la version historique du développement l'application{" "}
        <a href="http://siance.asn.i2">http://siance.asn.i2</a> est en train
        d'être remplacée progressivement par une nouvelle interface{" "}
        <a href="http://siance-preprod.asn.i2">http://siance-preprod.asn.i2</a>{" "}
        qui monte en charge progressivement auprès des directions et divisions.
      </QuestionItem>
      <Divider variant="inset" />
      <QuestionItem question="Comment fonctionne l’annotation dans SIANCE ?">
        En 2019 et 2020, des inspecteurs ont été sollicités pour annoter
        plusieurs milliers de lettres de suite suivant des ontologies définies
        conjointement par les bureaux, la MSC et le BIN. Aujourd'hui, grâce à
        ces annotations historiques, les nouvelles lettres de suite sont
        automatiquement annotées et classées par l'algorithme. Ces annotations
        permettent d'affiner la recherche des lettres de suite dans SIANCE et
        permettra prochainement de suivre des indicateurs thématiques calculés
        sur plusieurs années d'inspection.
      </QuestionItem>
      <Divider variant="inset" />
      <QuestionItem question="À qui s'adresse SIANCE ?">
        SIANCE a vocation à accompagner les processus d'inspection et
        d'évaluation des sites. L'outil est accessible à l'ensemble des
        inspecteurs, et peut être utilisé pour rechercher des lettres de suite,
        croiser des écarts observés sur différents sites, construire des bilans,
        etc.
      </QuestionItem>
      <Divider variant="inset" />
      <QuestionItem question="Puis-je participer aux orientations de SIANCE ?">
        SIANCE est développé en interne par l'ASN, et l'ensemble des divisions
        et des bureaux est chaleureusement invité à proposer des ajustements des
        interfaces et des algorithmes tout au long du développement de
        l'applicatio pour que celle-ci correspondent au mieux aux besoins
        spécifiques de chaque entité. L'ensemble de ces suggestions et demandes
        peut être adressé à la MSC et au BIN. Les bugs de l'outil (en cours de
        développement) peuvent être signalées pour correction à l'équipe de
        SIANCE par mail{" "}
        <a href="mailto:contact-siance@asn.fr">contact-siance@asn.fr</a> ou par
        téléphone.
      </QuestionItem>
    </List>
  );
}

function Referentials() {
  return (
    <Typography>
      Lors du développement de SIANCE nous avons produit un certain nombre de
      référentiels. Vous pouvez trouver{" "}
      <a href={`${conf.api.url}/referentials/referentiel_INB`}>
        notre référentiel INB
      </a>
      , le{" "}
      <a href={`${conf.api.url}/referentials/referentiel_hospitals`}>
        référentiel hôpitaux de Paris
      </a>
      , le{" "}
      <a href={`${conf.api.url}/referentials/referentiel_edf_trigrams`}>
        référentiel systèmes EDF
      </a>{" "}
      <a href={`${conf.api.url}/referentials/referentiel_isotopes`}>
        référentiel des isotopes
      </a>{" "}
      ou encore le{" "}
      <a href={`${conf.api.url}/referentials/referentiel_themes`}>
        référentiel des thèmes d'inspection
      </a>
      .
    </Typography>
  );
}

/* function intercalate<T>(array: T[], sep: T): T[] {
  return array.flatMap((x) => [sep, x]).slice(1);
} */

const useModalStyles = makeStyles((theme) => ({
  bigButton: {
    width: "100%",
    border: `2px solid ${theme.palette.primary.main}`,
    padding: theme.spacing(2),
    borderRadius: "10px 10px",
    color: theme.palette.primary.main,
    textAlign: "center",
    display: "grid",
    "&:hover": {
      textDecoration: "underline",
    },
    "& .icon .MuiSvgIcon-root": {
      fontSize: "5rem",
      gridRowStart: 1,
      gridRowEnd: 1,
    },
    "& .subheader": {
      display: "block",
      gridRowStart: 2,
      gridRowEnd: 2,
    },
  },
}));

type HugeModalAndButtonProps = {
  icon: React.ReactNode;
  desc: string;
  children: React.ReactNode;
};

function HugeModalAndButton({ icon, desc, children }: HugeModalAndButtonProps) {
  const [open, setOpen] = React.useState<boolean>(false);
  const styles = useModalStyles();
  return (
    <>
      <ButtonBase className={styles.bigButton} onClick={() => setOpen(true)}>
        <span className="icon">{icon}</span>
        <span className="subheader">{desc}</span>
      </ButtonBase>
      <Dialog color="primary" open={open} onClose={() => setOpen(false)}>
        <DialogTitle>{desc}</DialogTitle>
        <DialogContent>{children}</DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Fermer</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

function HelpSteps() {
  const { data: userConfig } = useUserConfig();
  const isAdmin = userConfig?.user.is_admin || false;
  const steps = Pages.filter((p) => isAdmin || !p.admin);
  const len = steps.length;

  const [activeStep, setActiveStep] = React.useState<number>(0);
  return (
    <>
      <Stepper color="primary" nonLinear activeStep={activeStep}>
        {steps.map((p, i) => (
          <Step key={p.name}>
            <StepButton
              icon={
                <Typography
                  color={i === activeStep ? "primary" : "textSecondary"}
                >
                  {p.icon}
                </Typography>
              }
              onClick={() => setActiveStep(i)}
            ></StepButton>
          </Step>
        ))}
      </Stepper>
      {steps[activeStep].content}
      <Box p={2}>
        <Divider />
      </Box>
      <Grid container spacing={1} justify="space-between">
        <Grid item xs={12} sm={3}>
          <Button
            disabled={activeStep === 0}
            onClick={() => setActiveStep(Math.max(0, activeStep - 1))}
          >
            Fonction précédente
          </Button>
        </Grid>
        <Grid item xs={12} sm={6}>
          <Typography color="primary" align="center" variant="subtitle1">
            {steps[activeStep].name}
          </Typography>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Button
            disabled={activeStep === len - 1}
            onClick={() => setActiveStep(Math.min(len - 1, activeStep + 1))}
          >
            Fonction suivante
          </Button>
        </Grid>
      </Grid>
    </>
  );
}

function Home() {
  const styles = useStyles();

  return (
    <Container className={styles.homeContainer}>
      <Box p={4}>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <HugeModalAndButton
              desc="Présentation de l'outil"
              icon={<DirectionsIcon />}
            >
              <Typography align="justify" gutterBottom>
                SIANCE est un outil développé par l’ASN qui a pour vocation
                d’aider la préparation et la planification des inspections en
                permettant d’exploiter pleinement les lettres de suite.
              </Typography>
              <HelpSteps />
            </HugeModalAndButton>
          </Grid>
          <Grid item xs={12} sm={6}>
          <HugeModalAndButton
              desc="Aide à la recherche"
              icon={<HelpOutlineIcon />}
            >
              <HelpDialog/>
            </HugeModalAndButton>
          </Grid>
          <Grid item xs={12} sm={6}>

            <HugeModalAndButton
              desc="L'ontologie utilisée par SIANCE"
              icon={<CategoryIcon />}
            >
              <Typography>
                SIANCE utilise un grand nombre de méta-données du SIv2, croisées
                avec les bases de l’INSEE et l’API <code>geo.api.gouv.fr</code>.
                Toutefois, pour simplifier les recherches et uniformiser les
                pratiques, une ontologie dédiée à SIANCE a été produite afin de
                classer <em>automatiquement</em> les lettres de suite. Cette
                ontologie se découpe en « catégorie » et « sous-catégorie ».
              </Typography>
              <DisplayCategories />
            </HugeModalAndButton>
          </Grid>
          <Grid item xs={12} sm={6}>
            <HugeModalAndButton
              desc="La Foire Aux Questions"
              icon={<ContactSupportIcon />}
            >
              <FAQ />
            </HugeModalAndButton>
          </Grid>
          <Grid item xs={12} sm={6}>
            <HugeModalAndButton desc="Référentiels" icon={<AssignmentIcon />}>
              <Referentials />
            </HugeModalAndButton>
          </Grid>
          <Grid item xs={12} sm={6}>
            <HugeModalAndButton
              desc="Contacts et retours d'expérience"
              icon={<ContactMailIcon />}
            >
              <Contact contacts={contacts} />
            </HugeModalAndButton>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
}

export default Home;
