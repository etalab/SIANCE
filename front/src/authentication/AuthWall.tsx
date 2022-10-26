import React from "react";

import { useUserConfig, useUserError, AuthError } from "./Utils";

import { AuthenticationForm } from "./Authentication";
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
} from "@material-ui/core";

const ErrorPrinter = ({
  connectionError,
  userError,
}: {
  connectionError: AuthError | null;
  userError: any;
}) => {
  const badCredentials = connectionError && connectionError.status === 401;
  const serverSideError = connectionError && connectionError.status !== 401;
  const invalidToken = userError && userError?.status === 401;

  if (badCredentials) {
    return (
      <Typography color="secondary">
        Le nom d'utilisateur ou le mot de passe est invalide.
        {JSON.stringify(connectionError)}
      </Typography>
    );
  } else if (serverSideError) {
    return (
      <Typography color="secondary">
        Une erreur est survenue sur le Serveur SIANCE (
        {JSON.stringify(serverSideError)}), il est possible que vous n'ayez pas
        activé votre VPN, si votre VPN est activé mais que l'erreur persiste
        contactez un administrateur.
      </Typography>
    );
  } else if (invalidToken) {
    return (
      <Typography color="secondary">
        Vous avez été déconnecté de SIANCE après une trop longue période
        d'inactivité.
      </Typography>
    );
  } else if (userError) {
    return (
      <Typography color="secondary">
        Impossible de récupérer les informations de votre compte (
        {JSON.stringify(userError)})
      </Typography>
    );
  } else {
    return <></>;
  }
};

const AuthWall = ({ children }: { children: React.ReactNode }) => {
  const error = useUserError();
  const {
    data: userConfig,
    isValidating,
    error: userConfigError,
  } = useUserConfig();

  const isFlickering =
    localStorage.getItem("jwt-token") !== undefined &&
    userConfig === undefined &&
    isValidating === true;

  const isNotLogged =
    !userConfig || userConfigError || (error && error.status !== 200);

  const shouldDisplayPopup = !isFlickering && isNotLogged;

  return (
    <>
      <Dialog open={shouldDisplayPopup ? true : false}>
        <DialogTitle>
          Connexion à SIANCE{" "}
          <span style={{ color: "#c30d0d", fontWeight: 1000 }}>DEV</span>
        </DialogTitle>
        <DialogContent>
          <Box m={2}>
            <AuthenticationForm />
          </Box>
          <Box m={2}>
            <ErrorPrinter connectionError={error} userError={userConfigError} />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button href="mailto:contact-siance@asn.fr">
            Contacter le support technique
          </Button>
          <Button href="/help">Consulter l'aide</Button>
        </DialogActions>
      </Dialog>
      {children}
    </>
  );
};

export default AuthWall;
