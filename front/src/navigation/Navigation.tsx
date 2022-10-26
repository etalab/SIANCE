import React, { FunctionComponent } from "react";

import { useStyles } from "./Styles";

import SianceDrawer from "./SianceDrawer";
import SianceAppBar from "./SianceAppBar";

interface PageProps {
  path: string;
  name: string;
  desc: string;
  inMenu: boolean;
  icon: React.ReactElement;
  admin: boolean;
}

type NavigationProps = {
  pages: PageProps[];
  children: React.ReactNode;
};

const Navigation: FunctionComponent<NavigationProps> = ({
  pages,
  children,
}) => {
  const styles = useStyles();

  const [menuOpen, setMenuOpen] = React.useState<boolean>(false);

  return (
    <div className={`${styles.root} ${menuOpen ? null : styles.rootClosed}`}>
      <SianceAppBar
        menuOpen={menuOpen}
        toggleNavigation={() => setMenuOpen(!menuOpen)}
      />
      <SianceDrawer pages={pages} menuOpen={menuOpen} />
      <main className={styles.content}>{children}</main>
    </div>
  );
};

export default Navigation;
