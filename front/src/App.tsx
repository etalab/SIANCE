import { Box, Container, Paper, Typography } from "@material-ui/core";
import orange from "@material-ui/core/colors/orange";
import teal from "@material-ui/core/colors/teal";
import {
  createMuiTheme,
  makeStyles,
  ThemeProvider,
} from "@material-ui/core/styles";
import "fontsource-roboto";
import React from "react";
import { BrowserRouter as Router, Route, Switch } from "react-router-dom";
import "./App.css";
import AuthWall from "./authentication/AuthWall";
import { AuthenticationProvider } from "./authentication/Utils";
import { SearchRequestProvider } from "./contexts/Search";
import { SeenLettersProvider } from "./searchPage/contexts/SeenDocuments";

import Navigation from "./navigation/Navigation";
import Pages from "./Pages";

const theme = createMuiTheme({
  palette: {
    primary: {
      main: teal[500],
    },
    secondary: {
      main: orange[800],
    },
  },
});

const useStyles = makeStyles(() => ({
  root: {
    "& a:visited": {
      color: teal[800],
    },
    "& a": {
      color: teal[500],
    },
    "& a:hover": {
      color: teal[200],
    },
  },
}));

const hasIE: boolean =
  window.navigator.userAgent.indexOf("Trident/") > 0 ? true : false;

function UseOtherBrowser() {
  return (
    <Container>
      <Box mt={5}>
        <Paper>
          <Box p={3}>
            <Typography variant="h3" color="secondary" gutterBottom>
              Le navigateur utilisé n'est pas officiellement supporté
            </Typography>
            <Typography variant="body1">
              Ouvrez le lien avec Mozilla Firefox, Google Chrome ou un
              navigateur qui n'est pas désuet.
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}


function Maintenance({date}: {date: string}) {
  return (
    <Container>
      <Box mt={5}>
        <Paper>
          <Box p={3}>
            <Typography variant="h3" color="secondary" gutterBottom>
              Opération de maintenance en cours
            </Typography>
            <Typography variant="body1">
              {
              "Le site subit actuellement une opération de maintenance" + (
                date? " jusqu'au " + date: ""
              ) + " et sera incessamment remis en service."
              }
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}


function App() {
  const styles = useStyles();
  

  if (hasIE) {
    return (
      <ThemeProvider theme={theme}>
        <UseOtherBrowser />
      </ThemeProvider>
    );
  }

  // when you want to launch a maintenance, you can modify the values below and push them in preprod/prod
  const isMaintenance = false;
  if (isMaintenance) {
    let endMaintenance = "samedi 2 octobre 12:00";
    return (
      <ThemeProvider theme={theme}>
        <Maintenance date={endMaintenance}/>
      </ThemeProvider>
    )
  }

  return (
    <ThemeProvider theme={theme}>
      <SeenLettersProvider>
        <div className={`App ${styles.root}`}>
          <Router>
            <AuthenticationProvider>
              <SearchRequestProvider>
                <Navigation pages={Pages}>
                  <Switch>
                    {Pages.map(
                      ({ component: Component, restricted, ...rest }) => (
                        <Route key={rest.path} {...rest}>
                          {restricted ? (
                            <AuthWall>
                              <Component />
                            </AuthWall>
                          ) : (
                            <Component />
                          )}
                        </Route>
                      )
                    )}
                  </Switch>
                </Navigation>
              </SearchRequestProvider>
            </AuthenticationProvider>
          </Router>
        </div>
      </SeenLettersProvider>
    </ThemeProvider>
  );
}

export default App;
