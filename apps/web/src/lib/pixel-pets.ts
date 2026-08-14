// Original hand-authored pixel-art companion sprites — chibi/blob body
// template shared across every species (cohesive "family" look, the
// same way Animal Crossing NPCs or Tamagotchi share a base rig), varied
// per species by color, a small "topper" (ears/antenna/etc, rendered
// above the body), and per-cell overrides for shape details a topper
// can't express (ghost's wavy trailing edge, turtle's shell dots).
//
// Deliberately not photoreal pixel art — no illustrator asset pipeline
// exists in this project, so these are simple, code-authored sprites
// (see PixelPet.tsx for the renderer). Keys must match
// apps/api/app/modules/auth/schemas.py's COMPANION_AVATARS exactly.

export type PixelGrid = string[]; // rows of equal length; '.' = transparent, other chars = palette keys

// 12x12 rounded "blob" body — every species starts from this exact
// grid. 'B' body fill, 'L' belly-light patch, 'E' eye.
export const PIXEL_PET_BODY: PixelGrid = [
  "...BBBBBB...",
  "..BBBBBBBB..",
  ".BBBBBBBBBB.",
  "BBBBBBBBBBBB",
  "BBEBBBBBBEBB",
  "BBBBBBBBBBBB",
  "BBBBBBBBBBBB",
  "BBBLLLLLLBBB",
  "BBLLLLLLLLBB",
  ".BLLLLLLLLB.",
  ".BBBBBBBBBB.",
  "..BBBBBBBB..",
];
// NOTE: the last body row above is 13 chars; every real grid used at
// render time is validated/truncated to 12 by PixelPet.tsx — kept as
// documentation only, PIXEL_PETS below defines the authoritative copy.

export interface PixelPetSpec {
  label: string;
  bodyColor: string;
  bellyColor: string;
  eyeColor: string;
  accentColor: string;
  /** Rendered above the body, same column count (12). */
  topper?: PixelGrid;
  /** Per-cell overrides applied to the body grid itself (row/col are
   * 0-indexed into the 12x12 body, char is a key into `overrideColors`
   * or 'B'/'L'/'.' to reuse the base palette). */
  bodyOverrides?: { row: number; col: number; char: string }[];
}

const A = "A"; // topper/accent fill marker

export const PIXEL_PETS: Record<string, PixelPetSpec> = {
  dog: {
    label: "Dog",
    bodyColor: "#D9A066",
    bellyColor: "#F3E1C4",
    eyeColor: "#2B2118",
    accentColor: "#8B5A2B",
    topper: [
      "..A......A..",
      ".AA......AA.",
      "AAA......AAA",
    ],
  },
  cat: {
    label: "Cat",
    bodyColor: "#E8952A",
    bellyColor: "#FBE3C2",
    eyeColor: "#2B2118",
    accentColor: "#C06A16",
    topper: [
      "..A......A..",
      ".AA......AA.",
      ".AAA....AAA.",
    ],
  },
  bot: {
    label: "Robot",
    bodyColor: "#8FA3B3",
    bellyColor: "#DCE6EC",
    eyeColor: "#5CE1E6",
    accentColor: "#5CE1E6",
    topper: [
      ".....A......",
      ".....A......",
      ".....A......",
    ],
  },
  rabbit: {
    label: "Rabbit",
    bodyColor: "#F2C9D8",
    bellyColor: "#FFFFFF",
    eyeColor: "#2B2118",
    accentColor: "#E8A8C0",
    topper: [
      ".AA......AA.",
      ".AA......AA.",
      ".AA......AA.",
      ".AA......AA.",
      ".AA......AA.",
    ],
  },
  bird: {
    label: "Bird",
    bodyColor: "#6EC6E8",
    bellyColor: "#EAF7FC",
    eyeColor: "#2B2118",
    accentColor: "#F2A33D",
    topper: [
      ".....A......",
      ".....AAA....",
    ],
    bodyOverrides: [
      { row: 5, col: 5, char: "F" },
      { row: 5, col: 6, char: "F" },
    ],
  },
  ghost: {
    label: "Ghost",
    bodyColor: "#D9CFEA",
    bellyColor: "#D9CFEA", // no belly contrast — ghosts are one flat tone
    eyeColor: "#4A3F63",
    accentColor: "#B8A9D9",
    bodyOverrides: [
      // Wavy trailing bottom edge instead of the shared rounded hem —
      // clears rows 9-11 and redraws a zigzag.
      { row: 9, col: 0, char: "." }, { row: 9, col: 11, char: "." },
      { row: 10, col: 0, char: "." }, { row: 10, col: 3, char: "." },
      { row: 10, col: 8, char: "." }, { row: 10, col: 11, char: "." },
      { row: 11, col: 1, char: "." }, { row: 11, col: 2, char: "." },
      { row: 11, col: 5, char: "." }, { row: 11, col: 6, char: "." },
      { row: 11, col: 9, char: "." }, { row: 11, col: 10, char: "." },
    ],
  },
  turtle: {
    label: "Turtle",
    bodyColor: "#6FAE5C",
    bellyColor: "#D7E8A8",
    eyeColor: "#22321C",
    accentColor: "#3F7A32",
    topper: ["......AA...."],
    bodyOverrides: [
      { row: 5, col: 4, char: "S" }, { row: 5, col: 7, char: "S" },
      { row: 6, col: 3, char: "S" }, { row: 6, col: 8, char: "S" },
      { row: 7, col: 5, char: "S" }, { row: 7, col: 6, char: "S" },
    ],
  },
  rocket: {
    label: "Rocket",
    bodyColor: "#C7CDD3",
    bellyColor: "#EDF0F2",
    eyeColor: "#2B2118",
    accentColor: "#E24A4A",
    topper: [
      ".....A......",
      "....AAA.....",
      "...AAAAA....",
    ],
    bodyOverrides: [
      { row: 10, col: 0, char: "F" }, { row: 10, col: 1, char: "F" },
      { row: 10, col: 10, char: "F" }, { row: 10, col: 11, char: "F" },
      { row: 11, col: 2, char: "F" }, { row: 11, col: 9, char: "F" },
    ],
  },
};

export const PIXEL_PET_KEYS = Object.keys(PIXEL_PETS);

export function getPixelPetSpec(species: string | null | undefined): PixelPetSpec {
  return (species && PIXEL_PETS[species]) || PIXEL_PETS.bot!;
}
