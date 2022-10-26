import { match, parse } from "./StringMatch";
import { expect } from "chai";

describe("parse", function () {
  it("should highlight a single partial match", function () {
    expect(parse("Hello world", [[0, 4]])).to.deep.equal([
      {
        text: "Hell",
        highlight: true,
      },
      {
        text: "o world",
        highlight: false,
      },
    ]);
  });

  it("should highlight a single complete match", function () {
    expect(parse("Hello world", [[0, 11]])).to.deep.equal([
      {
        text: "Hello world",
        highlight: true,
      },
    ]);
  });

  it("should highlight multiple non-consecutive matches", function () {
    expect(
      parse("Hello world", [
        [2, 4],
        [6, 8],
      ])
    ).to.deep.equal([
      {
        text: "He",
        highlight: false,
      },
      {
        text: "ll",
        highlight: true,
      },
      {
        text: "o ",
        highlight: false,
      },
      {
        text: "wo",
        highlight: true,
      },
      {
        text: "rld",
        highlight: false,
      },
    ]);
  });

  it("should highlight multiple consecutive matches", function () {
    expect(
      parse("Hello world", [
        [2, 4],
        [4, 8],
      ])
    ).to.deep.equal([
      {
        text: "He",
        highlight: false,
      },
      {
        text: "ll",
        highlight: true,
      },
      {
        text: "o wo",
        highlight: true,
      },
      {
        text: "rld",
        highlight: false,
      },
    ]);
  });

  it("should not highlight the text if there are no matches", function () {
    expect(parse("Hello world", [])).to.deep.equal([
      {
        text: "Hello world",
        highlight: false,
      },
    ]);
  });
});

describe("match", function () {
  it("should highlight at the beginning of a word", function () {
    expect(match("some text", "te")).to.deep.equal([[5, 7]]);
  });

  it("should not highlight at the middle of a word", function () {
    expect(match("some text", "e")).to.deep.equal([]);
  });

  it("should highlight all the matches when query has multiple words", function () {
    expect(match("some sweet text", "s s")).to.deep.equal([
      [0, 1],
      [5, 6],
    ]);
  });

  it("should highlight when case doesn't match", function () {
    expect(match("Some Text", "t")).to.deep.equal([[5, 6]]);
  });

  it("should remove diacritics when highlighting", function () {
    expect(match("Déjà vu", "deja")).to.deep.equal([[0, 4]]);
  });

  it("should highlight diacritics", function () {
    expect(match("Déjà vu", "déjà")).to.deep.equal([[0, 4]]);
  });

  it("should highlight special characters", function () {
    expect(match("highlight the & or not", "&")).to.deep.equal([[14, 15]]);
  });

  it("should ignore whitespaces in query", function () {
    expect(match("Very nice day", "\td   \n\n ver \t\t   ni \n")).to.deep.equal(
      [
        [0, 3],
        [5, 7],
        [10, 11],
      ]
    );
  });

  it("should not highlight anything if the query is blank", function () {
    expect(match("Very nice day", " ")).to.deep.equal([]);
  });

  it("should not merge the matches", function () {
    expect(match("Very nice day", "very nice day")).to.deep.equal([
      [0, 4],
      [5, 9],
      [10, 13],
    ]);
  });
});
