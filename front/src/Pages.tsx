import React from "react";

import Typography from "@material-ui/core/Typography";
import SearchIcon from "@material-ui/icons/Search";
import AssessmentIcon from '@material-ui/icons/Assessment';
import CreateIcon from "@material-ui/icons/Create";
import DescriptionIcon from "@material-ui/icons/Description";
import ShowChartIcon from "@material-ui/icons/ShowChart";
import HelpOutlineIcon from "@material-ui/icons/HelpOutline";
import PeopleIcon from "@material-ui/icons/People";
import AccountCircleIcon from '@material-ui/icons/AccountCircle';
//import EngineeringIcon from '@material-ui/icons/Engineering';
//import ManageAccountsIcon from '@material-ui/icons/ManageAccounts';
import MenuBookIcon from '@material-ui/icons/MenuBook';

import Home from "./homepage/Home";
import Help from "./help/Help";
import Observe from "./observe/Observe";
import Inpect from "./inspect/Inspect";
import Annotate from "./annotate/Annotate";
import Trends from "./trends/Trends";
import SearchInspection from "./searchPage/SearchPage";
import Admin from "./admin/Admin";
import UserPage from "./components/UserPage";
import Watch from "./watch/Watch"


import HomeIcon from "@material-ui/icons/Home";
import Dashboard from "./dashboard/Dashboard";
import SupervisorAccountIcon from "@material-ui/icons/SupervisorAccount";

import config from "./config.json";

export type PageElement = {
  path: string;
  name: string;
  icon: JSX.Element;
  desc: string;
  exact: boolean;
  component: () => JSX.Element;
  restricted: boolean;
  inMenu: boolean;
  admin: boolean;
  content: JSX.Element;
};

export const Accueil = {
  path: "/",
  name: "Accueil",
  icon: <HomeIcon />,
  desc: "Page d’accueil",
  exact: true,
  component: Home,
  restricted: true,
  inMenu: false,
  admin: false,
  content: (
    <Typography>
      Je suis sur la page principale de SIANCE, je m’informe sur son
      fonctionnement, sur ses objectifs et son utilisation. Pour bien commencer,
      je peux me renseigner sur <a href="#ontologie">l’ontologie utilisée</a>{" "}
      par SIANCE, ou regarder <a href="#faq">la foire aux questions</a>.
    </Typography>
  ),
};

export const Rechercher = {
  path: "/search",
  name: "Rechercher",
  icon: <SearchIcon />,
  desc: "Je trouve des lettres de suites correspondant à mes critères",
  exact: false,
  component: SearchInspection,
  inMenu: true,
  restricted: true,
  admin: false,
  content: (
    <Typography>
      Je recherche des lettres de suite pour préparer une inspection ou une synthèse
    </Typography>
  ),
};

export const Visualiser = {
  path: "/dashboard",
  name: "Visualiser",
  icon: <AssessmentIcon />,
  desc: "Je visualise la cartographie des inspections correspondant à mes résultats de recherche",
  component: Dashboard,
  exact: true,
  inMenu: true,
  restricted: true,
  admin: false,
  content: (
    <Typography>
      J'ai une représentation graphique de ma recherche
    </Typography>
  ),
};

export const Inspection = {
  path: "/inspect",
  name: "Inspecter",
  icon: <PeopleIcon />,
  desc: "Je consulte les derniers documents relatifs à un établissement ou à un thème",
  component: Inpect,
  exact: true,
  inMenu: true,
  restricted: true,
  admin: false,
  content: (
    <Typography>
      J'ai accès aux derniers documents relatifs
      à un établissement ou à un thème
    </Typography>
  ),
};

export const Observer = {
  path: "/find_letter",
  name: "Observer",
  icon: <DescriptionIcon />,
  desc: "J’observe une lettre en particulier",
  exact: true,
  inMenu: false,
  component: Observe,
  restricted: true,
  admin: false,
  content: (
    <Typography>
      J’utilise l’identifiant d’une lettre pour en récupérer le texte et les
      métadonnées enrichies par SIANCE. Je peux ainsi, parcourir rapidement la
      lettre pour savoir quelles sont les thèmes abordés, les demandes d’actions
      correctives, ainsi que des suggestions de recherche pour des documents
      similaires.
    </Typography>
  ),
};

export const Prévoir = {
  path: "/trends",
  name: "Tendances",
  icon: <ShowChartIcon />,
  desc: "J'observe des indicateurs macro",
  component: Trends,
  restricted: true,
  admin: false,
  inMenu: true,
  exact: true,
  content: (
    <Typography>
      J'observe des tendances globales
    </Typography>
  ),
};

export const Annoter = {
  path: "/annotate",
  name: "Annoter",
  icon: <CreateIcon />,
  desc: "J’aide l’algorithme en annotant des lettres de suite",
  component: Annotate,
  admin: false,
  inMenu: config.prod ? false : true, // l'annotation se fait uniquement en preprod (lieu des model training)
  restricted: true,
  exact: true,
  content: (
    <Typography>
      J’annote des lettres de suite afin d’améliorer globalement
      la qualité de l'outil.
    </Typography>
  ),
};

export const Administrer = {
  path: "/admin",
  name: "Administrer",
  icon: <SupervisorAccountIcon />,
  desc: "J’observe et administre la base de connaissance de siance",
  restricted: true,
  component: Admin,
  inMenu: true,
  admin: true,
  exact: true,
  content: (
    <Typography>
      J’observe et administre la base de connaissance de siance. Je peux aussi
      voir l’évolution des indicateurs d’utilisation de SIANCE.
    </Typography>
  ),
};

export const Aide = {
  path: "/help",
  name: "Aide",
  icon: <HelpOutlineIcon />,
  desc: "Comment utiliser SIANCE ?",
  exact: true,
  component: Help,
  restricted: false,
  admin: false,
  inMenu: true,
  content: (
    <Typography>
      Je me rends sur la page d'aide de SIANCE, je m’informe sur son
      fonctionnement, sur ses objectifs et son utilisation. Pour bien commencer,
      je peux me renseigner sur <a href="#ontologie">l’ontologie utilisée</a>{" "}
      par SIANCE, ou regarder <a href="#faq">la foire aux questions</a>.
    </Typography>
  ),
};

export const Utilisateur = {
  path: "/login",
  name: "Mon profil",
  icon: <AccountCircleIcon />,
  desc: "Gérer mes favoris",
  exact: true,
  component: UserPage,
  restricted: true,
  admin: false,
  inMenu: false,
  content: (
    <Typography>
      Je consulte mes recherches sauvegardées
    </Typography>
  ),
};

export const Veiller = {
  path: "/watch",
  name: "Veille",
  icon: <MenuBookIcon />,
  desc: "Effectuer un grand nombre de recherches en parallèle, à des fins de veille",
  exact: true,
  component: Watch,
  restricted: true,
  admin: false,
  inMenu: true,
  content: (
    <Typography>
      Je réalise une veille documentaire
    </Typography>
  ),
};
const Pages: PageElement[] = [
  Accueil,
  Rechercher,
  Visualiser,
  Veiller,
  Inspection,
  Prévoir,
  Observer,
  Annoter,
  Administrer,
  Aide,
  Utilisateur,
];

export default Pages;
