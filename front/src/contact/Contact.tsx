import React, { FunctionComponent } from "react";

import { makeStyles } from "@material-ui/core/styles";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import CardContent from "@material-ui/core/CardContent";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import Grid from "@material-ui/core/Grid";

const useStyles = makeStyles((theme) => {
  return {
    root: {
      minWidth: 275,
      margin: theme.spacing(1, 1, 1, 1),
    },
    bullet: {
      display: "inline-block",
      margin: "0 2px",
      transform: "scale(0.8)",
    },
    title: {
      fontSize: 14,
    },
    pos: {
      marginBottom: 12,
    },
  };
});

export type ProfContactProps = {
  name: string;
  email: string;
  description: string;
  picture: string;
  status: string;
  location: string;
};

export type ContactProps = {
  contacts: ProfContactProps[];
};

export const ProfContact: FunctionComponent<ProfContactProps> = ({
  name,
  email,
  description,
  location,
  status,
  picture,
}) => {
  const classes = useStyles();
  return (
    <Card className={classes.root} variant="outlined">
      <CardContent>
        <Typography
          className={classes.title}
          color="textSecondary"
          gutterBottom
        >
          {status}
        </Typography>
        <Typography variant="h5" component="h2">
          {name}
        </Typography>
        <Typography className={classes.pos} color="textSecondary">
          {location}
        </Typography>
        <Typography variant="body2" component="p">
          {description}
        </Typography>
      </CardContent>
      <CardActions>
        <Button
          style={{ marginLeft: "auto" }}
          size="small"
          variant="outlined"
          color="primary"
          href={`mailto:${email}`}
        >
          Contactez-moi
        </Button>
      </CardActions>
    </Card>
  );
};

const Contact: FunctionComponent<ContactProps> = ({ contacts }) => {
  return (
    <div>
      <Grid
        container
        direction="row"
        spacing={2}
        alignItems="center"
        justify="center"
      >
        {contacts.map((x) => (
          <Grid item xs key={x.name}>
            <ProfContact {...x} />
          </Grid>
        ))}
      </Grid>
    </div>
  );
};

export default Contact;
