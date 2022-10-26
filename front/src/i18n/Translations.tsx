/**
 * Design Choices
 *
 * 1. Use a const record so that typescript is able to infer the
 *    complete structure of the translator
 *
 * 2. Fix the Language properties, but allow for completely
 *    free structure in the translation scheme. This scheme
 *    will be used _later on_ and the errors will appear there.
 *
 * 3. This is because until now (March 2021)
 *    there is not yet a simple way to write
 *    Translations is of type Record<Language, T> where
 *    T has to be infered by the compiler
 *
 * -----
 *
 * The type constraints arise from the module ./i18n
 * that constraints the use of useTranslator
 * to objects of shape Record<Language, T>.
 *
 */

export type Language = "fr";

export const Translations = {
  fr: {
    filters: {
      equipments_trigrams: {
        short: "Systèmes (REP)",
        full: "Systèmes EDF détectés dans la lettre de suite",
      },
    },
    categories: {},
    regions: {},
  },
};

export default Translations;
