import React, { FunctionComponent } from "react";

import { Link as RouterLink } from "react-router-dom";

import { Button, Menu, MenuItem, makeStyles } from "@material-ui/core";

import AccountCircleIcon from "@material-ui/icons/AccountCircle";
import MeetingRoomIcon from "@material-ui/icons/MeetingRoom";
import SettingsIcon from "@material-ui/icons/Settings";

const useStyles = makeStyles((theme) => ({
  button: {
    color: theme.palette.primary.contrastText,
    borderColor: theme.palette.primary.contrastText,
  },
}));

type UserButtonProps = {
  isLogged: string | boolean;
  logout: () => void;
};

const UserButton: FunctionComponent<UserButtonProps> = ({
  logout,
  isLogged,
}) => {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const classes = useStyles();

  const handleClick = (
    event: React.MouseEvent<HTMLButtonElement, MouseEvent>
  ) => {
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
    logout();
  };

  return (
    <>
      {isLogged ? (
        <Button
          className={classes.button}
          onClick={handleClick}
          variant="outlined"
          aria-haspopup="true"
          aria-controls="simple-menu"
          startIcon={<AccountCircleIcon />}
        >
          {isLogged}
        </Button>
      ) : null}
      <Menu
        id="user-menu"
        anchorEl={anchorEl}
        keepMounted
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem component={RouterLink} to="/login">
          <SettingsIcon /> Mon profil
        </MenuItem>
        <MenuItem onClick={handleClose}>
          <MeetingRoomIcon /> Déconnexion
        </MenuItem>
      </Menu>
    </>
  );
};

export default UserButton;
