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
} from "@material-ui/core";

import { makeStyles } from "@material-ui/core/styles";

import { useUserConfig, useLogin, useUserError } from "./Utils";

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

const Authentication = () => {
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
    <Container maxWidth="sm">
      <Box m={2} p={2}>
        <Paper className={styles.paperBlock}>
          <Typography variant="subtitle1" gutterBottom>
            {isLogged
              ? "Vous êtes actuellement connecté à SIANCE"
              : "Vous n'êtes pas connecté à SIANCE"}
          </Typography>
          <Divider />
          <Box mt={2} mb={3}>
            <Typography variant="h6">Connexion à SIANCE</Typography>
            <Typography variant="subtitle2">
              Votre nom d’utilisateur et votre mot de passe sont identiques à
              ceux d’Oasis.
            </Typography>
            <AuthenticationForm />
          </Box>
          <Divider />
          <List>
            <ListItem>
              <ListItemText
                primary="Nom d'utilisateur"
                secondary={userConfig?.user.fullname || "non connecté"}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="En cours de connexion ?"
                secondary={`${userConfigIsValidating}`}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Ticket unique de connexion"
                secondary={`${window.localStorage
                  .getItem("jwt-token")
                  ?.slice(0, 10)}...`}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Erreur de connexion (préférences utilisateur)"
                secondary={`${userConfigError}`}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Erreur d'authentification"
                secondary={`${JSON.stringify(userError)}`}
              />
            </ListItem>
          </List>
        </Paper>
      </Box>
    </Container>
  );
};

export default Authentication;
