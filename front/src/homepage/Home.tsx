import React from "react";

import {
  Box,
  Typography,
  Grid,
  Tab
} from "@material-ui/core";

import Pages from "../Pages";

import { useUserConfig } from "../authentication/Utils";
import { Link as RouterLink } from "react-router-dom";

function Home(){
  const { data: userConfig } = useUserConfig();

  const getInnerText = function(c: string | object | JSX.Element): string{
    if ((c as any).props && (c as any).props.children) {
      return getInnerText((c as any).props.children)
    } else if (typeof(c)==="string") {
      return c
    } else if (Array.isArray(c)) {
        return (c as any).map(getInnerText).join(" ")
    } else {
      return ""
    }
  }
  return (
    <Grid container direction="column" >
      <img alt="SIANCE ASN" src="/home/rapport-asn-mini.jpg"/>
      <Grid item>
        <Typography variant="h4" align="center">
          Bienvenue sur SIANCE <em>{userConfig?.user.fullname}</em>
        </Typography>
        </Grid>

    <Grid container direction="row"  >
    <Grid item alignItems="center" sm={1}>
    </Grid>

    {

        Pages.map((p) => {
          const innerText = getInnerText(p.content)
            return (
            p.inMenu && p.name !== "Aide" && p.name !== "Annoter" && !p.admin ? (
              <Grid item container direction="column" sm={2} alignItems="center">
                <Grid>
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
              </Grid>
              <Grid>
                <Box m={1}>
                  <div title={innerText.length>200? innerText: ""} className="text-align:center;">
                    {innerText.length > 200 ?
                    innerText.slice(0,200)+"..." : innerText}
                  </div>
                </Box>
                </Grid>
              </Grid>
            ) : null
          )
        })
    }
    </Grid>

    </Grid>
  )
}

export default Home;
