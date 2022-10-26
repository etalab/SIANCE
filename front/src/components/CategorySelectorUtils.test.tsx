import { expect } from "chai";

import { searchParts } from "./CategorySelectorUtils";

describe("searchParts", function () {
  it("should recognise partial matches", () => {
    expect(searchParts("search", "I am searching parts")).to.deep.equal([
      [
        {
          text: "I am ",
          highlight: false,
        },
        {
          text: "search",
          highlight: true,
        },
        {
          text: "ing parts",
          highlight: false,
        },
      ],
      true,
    ]);
  });
  it("should recognise multiple matches", () => {
    expect(
      searchParts("search", "I am search search search parts")
    ).to.deep.equal([
      [
        {
          text: "I am ",
          highlight: false,
        },
        {
          text: "search",
          highlight: true,
        },
        {
          text: " ",
          highlight: false,
        },
        {
          text: "search",
          highlight: true,
        },
        {
          text: " ",
          highlight: false,
        },
        {
          text: "search",
          highlight: true,
        },
        {
          text: " parts",
          highlight: false,
        },
      ],
      true,
    ]);
  });
});
