import React from "react";

import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
  Button,
} from "@material-ui/core";

import useInspectDisplay, {
  useInspectDispatchDisplay,
} from "./contexts/Displays";

export default function HelpDialog() {
  let [open, setOpen] = React.useState(true)
  let { showHelp } = useInspectDisplay();
  const dispatch = useInspectDispatchDisplay();

  const quit = () => {
    setOpen(false)
    try{
      dispatch({ type: "HIDE_HELP" });
    } catch(e) {
      console.log(e)
    }
  }

  return (
    <Dialog
      onClose={quit}
      aria-labelledby="help-search"
      maxWidth="sm"
      open={open || showHelp}
      scroll="paper"
    >
      <DialogTitle color="primary" id="help-search-title">
        Comment utiliser la recherche
      </DialogTitle>
      <DialogContent dividers>
        <Typography variant="h5" color="primary">
          Le concept
        </Typography>
        <Typography>
          J’utilise le système de requêtes ci-après pour explorer les différents
          champs dans la base de données <code>siancedb</code>. Cette table
          contient les lettres exportées sur{" "}
          <a href="https://asn.fr">le site internet de l’ASN</a> avec des
          méta-données extraites du SIv2.
        </Typography>
        <Typography variant="h5" color="primary">
          La barre de recherche
        </Typography>
        <Typography>
          Je peux rechercher du texte arbitraire dans les lettres de suite en
          écrivant ma recherche puis en tapant ENTRÉE. 
          Dans la barre de recherche, je peux utiliser des opérateurs logiques ET (symbole &) et
          OU (symbole |). Je peux forcer la recherche d'une expression précise en l'entourant de
          guillements doubles.  
        </Typography>
        <Typography variant="h5" color="primary">
          Les filtres
        </Typography>
        <Typography>
          Je peux utiliser des filtres issus du panneau des filtres à gauche,
          ou restreindre ma recherche à un secteurs (REP/LUDD/NPX/TSR/ESP) en cliquant
          sur le bouton dans la partie gauche de la barre de recherche.
        </Typography>
        <Typography variant="h5" color="primary">
          Sélectionner une période de recherche
        </Typography>
        <Typography>
          Lorsque je veux contraindre la période, je la sélectionne en "glisser-déposer"
          sur le graphe "Temporalité des résultats". Je peux également cliquer sur le 
          calendrier pour sélectionner les dates de début et de fin.
          Par défaut, la recherche se fait sur les deux dernières années.
        </Typography>
        <Typography variant="h5" color="primary">
          Les cartes-résultats
        </Typography>
        <Typography>
          Je peux ouvrir une lettre en cliquant sur son nom.
          Je peux également la télécharger, obtenir son lien SIv2 ou voir pourquoi ce résultat 
          m'est renvoyé, grâce aux boutons en bas de la carte-résultat.
          Il est possible d'ordonner les résultats par pertinence, ou par date (croissante ou décroissante).
        </Typography>

        {/*}
        <Typography>
          Après ma première recherche, des suggestions sont générées à partir
          des résultats et je peux les sélectionner pour affiner ma recherche.
          En cliquant sur une suggestion, cela me permet de contraindre un champ
          spécifique du SIv2. Par exemple: <code>entité responsable</code>,{" "}
          <code>interlocuteur</code> ou <code>palier</code>.
        </Typography>
        */}
        <Typography>
          Si je désire utiliser un champ du SIv2 qui n’est pas présent, il
          suffit de contacter{" "}
          <a href="mailto:contact-siance@asn.fr">
            l’équipe de développement de siance
          </a>{" "}
          parvenir ma requête.
        </Typography>
        <Typography variant="h5" color="primary">
          Comment utiliser l’apprentissage
        </Typography>
        <Typography>
          Grâce à l’annotation d’environ 4000 lettres de suite par des
          inspecteurs, le moteur de recherche est capable de détecter des
          lettres qui se rapportent à certaines catégories pré-établies. 
          Contacter l'équipe de développement pour de plus amples informations.
        </Typography>
        <Typography>
          Ces catégories détectées dans les lettres sont utilisées implicement 
          dans le moteur de recherche. Il est aussi possible de sélectionner explicitement
          une catégorie dans la barre des filtres.
          Lorsqu'on lit une lettre dans SIANCE, on peut afficher les catégories prédites, 
          la couleur indique alors le niveau de fiabilité de la détection selon l'algorithme prédictif.  
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={quit} variant="outlined" color="primary">
          J’ai compris
        </Button>
      </DialogActions>
    </Dialog>
  );
}
