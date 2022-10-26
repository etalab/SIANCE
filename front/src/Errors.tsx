import React from "react";

import MuiAlert, { AlertProps } from "@material-ui/lab/Alert";
import Snackbar from "@material-ui/core/Snackbar";

export default function Alert(props: AlertProps) {
  return <MuiAlert elevation={6} variant="filled" {...props} />;
}

// import { ErrorBoundary, FallbackProps } from "react-error-boundary";

// function AdminErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
//   return (
//     <Typography color="secondary">
//       Une erreur est survenue, <pre>{error?.message}</pre>.
//       <Button onClick={resetErrorBoundary}> réessayer</Button>
//     </Typography>
//   );
// }

export type ErrorNotificationProps = {
  open: boolean;
  autoHideDuration?: number;
  message: React.ReactNode | string;
};

export function InfoNotification({
  open,
  autoHideDuration,
  message,
}: ErrorNotificationProps) {
  return (
    <Snackbar open={open} autoHideDuration={autoHideDuration}>
      <Alert severity="info">{message}</Alert>
    </Snackbar>
  );
}

export function ErrorNotification({
  open,
  autoHideDuration,
  message,
}: ErrorNotificationProps) {
  return (
    <Snackbar open={open} autoHideDuration={autoHideDuration}>
      <Alert severity="error">{message}</Alert>
    </Snackbar>
  );
}
