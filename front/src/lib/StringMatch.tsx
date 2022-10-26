import React from "react";

export function HighlightedTextDisplay({
  textDisplay,
}: {
  textDisplay: HighlightedText[];
}) {
  return (
    <React.Fragment key={textDisplay.map((t) => t.text).join()}>
      {textDisplay.map(({ text, highlight }, i) => (
        <span key={i} style={{ fontWeight: highlight ? 1000 : 400 }}>
          {text}
        </span>
      ))}
    </React.Fragment>
  );
}

const specialCharsRegex = /[.*+?^${}()|[\]\\]/g;
const wordCharacterRegex = /[a-z0-9_]/i;

export type HighlightedText = {
  text: string;
  highlight: boolean;
};

function parse(text: string, matches: [number, number][]): HighlightedText[] {
  const results = [[0, 0], ...matches, [text.length, text.length]];
  return results
    .map((value, i) =>
      i === 0 // first element has no block before
        ? [{ text: text.slice(value[0], value[1]), highlight: true }]
        : [
            {
              text: text.slice(results[i - 1][1], value[0]),
              highlight: false,
            },
            {
              text: text.slice(value[0], value[1]),
              highlight: true,
            },
          ]
    )
    .flat()
    .filter((v) => v.text.length > 0);
}

function normalize(str: string): string {
  return str
    .normalize("NFD")
    .replace("’", "'")
    .replace(/[\u0300-\u036f]/g, "");
}

function escapeRegexCharacters(str: string): string {
  return str.replace(specialCharsRegex, "\\$&");
}

function startsWithSpecialCharacter(str: string): boolean {
  return str.length > 0 && !wordCharacterRegex.test(str[0]);
}

function preMatch(
  text: string,
  query: string
): { text: string; queries: string[] } {
  const normalized_query = normalize(query);

  const substring_regex = new RegExp(/".*"/gi);
  const substring_queries: string[] = [];

  const query_without_substrings = normalized_query.replace(
    substring_regex,
    (match) => {
      substring_queries.push(match.slice(1, match.length - 1));
      return "";
    }
  );
  return {
    text: normalize(text),
    queries: [
      ...substring_queries,
      ...query_without_substrings
        .split(/(\s|\t|\n)+/)
        .map((x) => x.trim())
        .filter((v) => v.length > 0)
        .map((v) =>
          startsWithSpecialCharacter(v)
            ? escapeRegexCharacters(v)
            : `\\b${escapeRegexCharacters(v)}`
        ),
    ],
  };
}

function match(text: string, query: string): [number, number][] {
  const { queries, text: normalized_text } = preMatch(text, query);

  const normalized_query_regex = queries.join("|");

  if (normalized_query_regex === "") {
    return [];
  }

  const re = new RegExp(normalized_query_regex, "ig");

  const output: [number, number][] = [];

  normalized_text.replace(re, (match, index) => {
    output.push([index, index + match.length]);
    return "";
  });
  return output;
}

export { match, parse };
