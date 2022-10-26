import { makeStyles } from "@material-ui/core";

export const drawerWidth = 160;
export const useStyles = makeStyles((theme) => ({
  root: {
    display: "grid",
    height: "100vh",
    gridTemplateColumns: `${drawerWidth}px auto`,
    gridTemplateRows: "auto 1fr",
    transition: theme.transitions.create(["grid-template-columns"], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
  },
  rootClosed: {
    display: "grid",
    gridTemplateColumns: "0px auto",
    transition: theme.transitions.create(["grid-template-columns"], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
  },
  drawer: {
    textAlign: "center",
    gridColumn: 1,
    gridRow: "1 / 2",
  },
  content: {
    overflowY: "scroll",
    scrollBehavior: "smooth",
    width: "100%",
    gridColumn: 2,
    gridRow: 2,
  },
}));
