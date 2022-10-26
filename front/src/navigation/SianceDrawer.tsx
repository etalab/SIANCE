import React, { FunctionComponent } from "react";
import { Link as RouterLink, useLocation, useHistory } from "react-router-dom";

import { Button, Tabs, Tab, Grid, Drawer, Box } from "@material-ui/core";

import { useUserConfig } from "../authentication/Utils";

import { useStyles } from "./Styles";

interface PageProps {
  path: string;
  name: string;
  desc: string;
  inMenu: boolean;
  icon: React.ReactElement;
  admin: boolean;
}

type SianceDrawerProps = {
  menuOpen: boolean;
  pages: PageProps[];
  orientation?: "vertical" | "horizontal"
};
const SianceDrawer: FunctionComponent<SianceDrawerProps> = ({
  menuOpen,
  pages,
  orientation="vertical" // orientation of Tabs (vertical | horizontal)
}) => {
  const styles = useStyles();
  const history = useHistory();
  const location = useLocation();
  const locationpath = location.pathname;

  const { data: userConfig } = useUserConfig();
  const isLogged = userConfig ? userConfig.user.fullname : false;
  const isAdmin = userConfig && isLogged && userConfig.user.is_admin;

  return (
    <Drawer
      className={styles.drawer}
      anchor="left"
      variant="persistent"
      open={menuOpen}
    >
      <Box mt={1} mb={1} style={{ textAlign: "center", width: "100%" }}>
        <Button
          href="/"
          onClick={(e) => {
            e.preventDefault();
            history.push("/", history.location.state);
          }}
        >
          <img alt="SIANCE ASN" src="/siance.png" height="40" />
        </Button>
      </Box>
      <Grid
        container
        direction="column"
        justify="space-around"
        alignItems="baseline"
      >
        <Grid item>
          <Tabs
            value={
              pages.find((p) => p.inMenu && p.path === locationpath)
                ? locationpath
                : false
            }
            orientation={orientation}
            variant="fullWidth"
            aria-label="navigation tabs"
            indicatorColor="secondary"
            textColor="secondary"
            TabIndicatorProps={{style: {background:'secondary'}}}
          >
            {pages.map((p) =>
              p.inMenu && (!p.admin || isAdmin) ? (
                <Tab
                  key={p.path}
                  component={RouterLink}
                  to={p.path}
                  label={p.name}
                  icon={p.icon}
                  value={p.path}
                  title={p.desc}
                  aria-label={p.desc}
                />
              ) : null
            )}
          </Tabs>
        </Grid>
      </Grid>
    </Drawer>
  );
};

export default SianceDrawer;
