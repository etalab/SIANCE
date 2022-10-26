import React, { FunctionComponent } from "react";

import MenuIcon from "@material-ui/icons/Menu";

import { Grid, Toolbar, IconButton, makeStyles } from "@material-ui/core";

import UserButton from "./UserButton";
import SearchBar from "../components/Search";
import { useUserConfig, useLogout } from "../authentication/Utils";

export const useStyles = makeStyles((theme) => ({
  appBar: {
    boxShadow: "none",
    // borderBottom: `1px solid ${theme.palette.grey["100"]}`,
    backgroundColor: theme.palette.primary.dark,
    color: theme.palette.primary.contrastText,
  },
  menuOpen: {
    transition: theme.transitions.create(["transform"], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    transform: "rotate(90deg)",
  },
  menuClosed: {
    transition: theme.transitions.create(["transform"], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
    transform: "rotate(0deg)",
  },
}));

type SianceAppBarProps = {
  toggleNavigation: () => void;
  menuOpen: boolean;
};
const SianceAppBar: FunctionComponent<SianceAppBarProps> = ({
  toggleNavigation,
  menuOpen,
}) => {
  const { data: userConfig } = useUserConfig();

  const styles = useStyles();

  const isLogged = userConfig ? userConfig.user.fullname : false;

  const logout = useLogout();

  return (
    <div className={styles.appBar}>
      <Toolbar>
        <Grid container justify="space-between" alignItems="center">
          <Grid item>
            <IconButton edge="start" onClick={toggleNavigation}>
              <MenuIcon
                fontSize="small"
                className={[
                  styles.appBar,
                  menuOpen ? styles.menuOpen : styles.menuClosed,
                ].join(" ")}
              />
            </IconButton>
          </Grid>
          <Grid item xs={7} sm={6}>
            <SearchBar />
          </Grid>
          <Grid item xs={1} sm="auto">
            <UserButton isLogged={isLogged} logout={logout} />
          </Grid>
        </Grid>
      </Toolbar>
    </div>
  );
};

export default SianceAppBar;
