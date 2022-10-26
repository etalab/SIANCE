export type ELetter = {
  id_letter: number;
  name: string;
  content: string;
  date: Date;
  site_name: string[];
  complementary_site_name: string;
  interlocutor_name: string;
  interlocutor_city: string;
  identifiers: number[];
  theme: string;
  sectors: string[];
  domains: string[];
  natures: string[];
  pilot_entity: string;
  resp_entity: string;
  demands_a: number;
  demands_b: number;
  synthesis_topics: string[];
  demands_a_topics: string[];
  demands_b_topics: string[];
  observations_topics: string[];
  topics: string[];
  equipments_trigrams: string[];
  isotopes: string[];
  equipments_full_names: string[];
  siv2?: string;
  region?: string;
};

export const sampleLetter: ELetter = {
  id_letter: 2,
  name: "test",
  content: "test",
  date: new Date(),
  site_name: ["test1", "test2"],
  complementary_site_name: "test",
  interlocutor_name: "test",
  interlocutor_city: "test",
  identifiers: [2],
  theme: "test",
  sectors: ["test1", "test2"],
  domains: ["test1", "test2"],
  natures: ["test1", "test2"],
  pilot_entity: "test",
  resp_entity: "test",
  demands_a: 2,
  demands_b: 2,
  synthesis_topics: ["test1", "test2"],
  demands_a_topics: ["test1", "test2"],
  demands_b_topics: ["test1", "test2"],
  observations_topics: ["test1", "test2"],
  topics: ["test1", "test2"],
  equipments_trigrams: ["test1", "test2"],
  equipments_full_names: ["test1", "test2"],
  isotopes: ["isotope1", "isotope2"],
  siv2: "test",
};
