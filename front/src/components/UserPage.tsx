import React from "react";

import {
  Paper,
  TextField,
  Grid,
  Button,
  Typography,
  Box,
  Container,
  List,
  ListItem,
  ListItemText,
  Divider,
  ListItemSecondaryAction,
  Badge,
} from "@material-ui/core";

import { makeStyles } from "@material-ui/core/styles";

import useSavedSearches from "../hooks/UseUserSearch";

import { useUserConfig, useLogin, useUserError } from "../authentication/Utils";

const useStyles = makeStyles((theme) => ({
  paperBlock: {
    padding: theme.spacing(2),
  },
  grayed: {
    filter: "blured(1px)",
  },
}));

export const AuthenticationForm = () => {
  const [password, setPassword] = React.useState<string>("");
  const [username, setUsername] = React.useState<string>("");
  const login = useLogin();

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        login(username, password);
      }}
      autoComplete="off"
    >
      <Grid
        container
        direction="column"
        justify="center"
        spacing={3}
        className="login-form"
      >
        <Grid item>
          <TextField
            id="username"
            fullWidth
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Nom d’utilisateur"
            variant="outlined"
            required
            autoFocus
          />
        </Grid>
        <Grid item>
          <TextField
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            placeholder="Mot de passe"
            variant="outlined"
            fullWidth
            required
          />
        </Grid>
        <Grid item style={{ textAlign: "center" }}>
          <Button type="submit" variant="contained" fullWidth color="primary">
            Se connecter
          </Button>
        </Grid>
      </Grid>
    </form>
  );
};

export const SavedSearches = () => {
  const {
    data: savedSearches,
    handleDelete,
    handleResearch,
  } = useSavedSearches();

  if (savedSearches === undefined) {
    return <></>;
  }

  return (
    <>
      <Typography variant="h5" gutterBottom>
        Mes recherches enregistrées
      </Typography>
      <List>
        {savedSearches.length === 0 && (
          <ListItem>
            <ListItemText primary="Aucune recherche enregistrée" />
          </ListItem>
        )}
        {savedSearches
          .sort(
            (a, b) =>
              a.new_results - b.new_results ||
              new Date(a.stored_search.last_seen).getTime() -
                new Date(b.stored_search.last_seen).getTime()
          )
          .map((v) => (
            <ListItem
              button
              onClick={handleResearch(v)}
              key={v.stored_search.id_stored_search}
            >
              <ListItemText
                primary={
                  <>
                    <Badge
                      color="secondary"
                      anchorOrigin={{
                        vertical: "top",
                        horizontal: "left",
                      }}
                      max={99}
                      badgeContent={v.new_results}
                    >
                      {v.stored_search.name}
                    </Badge>
                  </>
                }
                secondary={
                  <>
                    Observée dernièrement le{" "}
                    {new Date(v.stored_search.last_seen).toLocaleString()}
                  </>
                }
              />
              <ListItemSecondaryAction>
                <Button onClick={handleDelete(v)}>Supprimer</Button>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
      </List>
    </>
  );
};

const UserPage = () => {
  const {
    data: userConfig,
    isValidating: userConfigIsValidating,
    error: userConfigError,
  } = useUserConfig();

  const userError = useUserError();

  const styles = useStyles();

  const isLogged =
    userConfig && !userConfigIsValidating && !userConfigError && !userError;

  return (
    <Container maxWidth="md">
      <Box m={2} p={2}>
        <Paper className={styles.paperBlock}>
          {isLogged ? (
            <Typography variant="subtitle1" gutterBottom>
              Vous êtes actuellement connecté à SIANCE
            </Typography>
          ) : (
            <>
              <Typography variant="subtitle1" gutterBottom>
                Connectez-vous à SIANCE pour accéder à vos informations.
              </Typography>
              <Divider />
              <Box mt={2} mb={3}>
                <Typography variant="h6">Connexion à SIANCE</Typography>
                <Typography variant="subtitle2">
                  Votre nom d’utilisateur et votre mot de passe sont identiques
                  à ceux d’Oasis.
                </Typography>
                <AuthenticationForm />
              </Box>
            </>
          )}
          <Divider />
          <List>
            <ListItem>
              <ListItemText
                primary="Nom d'utilisateur"
                secondary={userConfig?.user.fullname || "non connecté"}
              />
            </ListItem>
          </List>
          <SavedSearches />
        </Paper>
      </Box>
    </Container>
  );
};

export default UserPage;
