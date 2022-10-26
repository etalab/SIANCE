import React from "react";

import {
  Container,
  Typography,
  Grid,
  Button,
  Dialog,
  DialogTitle,
  DialogActions,
  DialogContent,
  Box,
  CircularProgress,
} from "@material-ui/core";

import CMeter from "./CMeter";
import DbStatus from "./DbStatus";
// import MLStatus from "./MLStatus";
import Radial from "../graphs/radial/Radial";

import useProjectIndicators from "../hooks/UseProjectIndicators";

function AdminHelp() {
  return <Typography>À rédiger</Typography>;
}

function UserStats() {
  const { data: projectIndicators } = useProjectIndicators();

  if (!projectIndicators) {
    return <CircularProgress />;
  }

  return (
    <Grid container>
      <Grid item sm={12} md={6}>
        <CMeter
          maxUsers={400}
          text="Suivi des utilisateurs"
          weekUsers={projectIndicators.weekUsers}
          monthUsers={projectIndicators.monthUsers}
          launchUsers={projectIndicators.launchUsers}
        />
      </Grid>
      <Grid item sm={12} md={6}>
        <CMeter
          maxUsers={projectIndicators.launchTraffic?projectIndicators.launchTraffic:2000}
          text="Suivi des connexions"
          weekUsers={projectIndicators.weeklyTraffic}
          monthUsers={projectIndicators.monthlyTraffic}
          launchUsers={projectIndicators.launchTraffic}
        />
      </Grid>
      <Grid item sm={12} md={6}>
        <Typography>
          Utilisation relative des fonctionnalités d'export. La zone bleue
          correspond au premier quartile (25%) du nombre d'usages sur le denier
          mois de la fonctionnalité considérée (en considérant seulement les
          usagers actifs ce mois). La zone rouge représente le second quartile,
          et la zone orange le troisième.
        </Typography>
        <Radial
          areas={["75%", "50%", "25%"]}
          vprops={{
            "50%": { color: "red" },
            "25%": { color: "blue" },
            "75%": { color: "orange" },
          }}
          series={projectIndicators.exportSeries}
        />
      </Grid>
      <Grid item sm={12} md={6}>
        <Typography>
          Utilisation relative de certains filtres dans les requêtes. La légende
          est la même que pour les fonctionnalités d'export.
        </Typography>
        <Radial
          areas={["75%", "50%", "25%"]}
          vprops={{
            "50%": { color: "red" },
            "25%": { color: "blue" },
            "75%": { color: "orange" },
          }}
          series={projectIndicators.filterSeries}
        />
      </Grid>
    </Grid>
  );
}

function Admin() {
  const [showHelp, setShowHelp] = React.useState<boolean>(false);

  return (
    <Container>
      <Box p={2}>
        <Grid container spacing={2} justify="space-evenly">
          <Grid item md={6} sm={12}>
            <Typography variant="h4">État de la base de données</Typography>
            <DbStatus />
          </Grid>
          <Grid item sm={12}>
            <Typography variant="h4">Statistiques d'utilisation</Typography>
            <UserStats />
          </Grid>
        </Grid>
      </Box>
      <Dialog open={showHelp} onClose={() => setShowHelp(false)}>
        <DialogTitle title="Aide" />
        <DialogContent>
          <AdminHelp />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowHelp(false)}>J'ai compris</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default Admin;
