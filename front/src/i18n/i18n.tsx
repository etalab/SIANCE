//import React from "react";

import { Language } from "./Translations";

const useCurrentLang = (): Language => {
  return "fr";
};

export default function useTranslator<T>(t: Record<Language, T>): T {
  return t[useCurrentLang()];
}
