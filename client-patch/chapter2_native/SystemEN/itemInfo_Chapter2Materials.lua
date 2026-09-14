-- Clean-room display metadata for twelve existing Chapter 2 server materials.
-- Names/type/weight follow effective Renewal item_db; translations remain TODO.
-- EpisodClear20 is an existing generic icon/sprite in the supplied data.grf.
-- No official Chapter 2 artwork, item effects, or acquisition rules are implied.
-- Separate optional import table; this file is NOT automatically installed.
tbl_chapter2materials = {
  [1002700] = {
    unidentifiedDisplayName = "Flame Gold Coin",
    unidentifiedResourceName = "EpisodClear20",
    unidentifiedDescriptionName = { "" },
    identifiedDisplayName = "Flame Gold Coin",
    identifiedResourceName = "EpisodClear20",
    identifiedDescriptionName = {
      "Chapter 2 native enchant material.",
      "Type: Etc",
      "Weight: 0",
      "^777777Generic compatibility icon; server label.^000000"
    },
    slotCount = 0, ClassNum = 0, costume = false
  },
  [1002751] = {
    unidentifiedDisplayName = "Blue Paper",
    unidentifiedResourceName = "EpisodClear20",
    unidentifiedDescriptionName = { "" },
    identifiedDisplayName = "Blue Paper",
    identifiedResourceName = "EpisodClear20",
    identifiedDescriptionName = {
      "Chapter 2 native enchant material (Ch2_Kindle_Hal_B).",
      "Type: Etc",
      "Weight: 0.1",
      "^777777Generic compatibility icon; server label.^000000"
    },
    slotCount = 0, ClassNum = 0, costume = false
  },
  [1002752] = {
    unidentifiedDisplayName = "Red Paper",
    unidentifiedResourceName = "EpisodClear20",
    unidentifiedDescriptionName = { "" },
    identifiedDisplayName = "Red Paper",
    identifiedResourceName = "EpisodClear20",
    identifiedDescriptionName = {
      "Chapter 2 native enchant material (Ch2_Kindle_Hal_R).",
      "Type: Etc",
      "Weight: 0.1",
      "^777777Generic compatibility icon; server label.^000000"
    },
    slotCount = 0, ClassNum = 0, costume = false
  },
  [1002753] = {
    unidentifiedDisplayName = "Yellow Paper",
    unidentifiedResourceName = "EpisodClear20",
    unidentifiedDescriptionName = { "" },
    identifiedDisplayName = "Yellow Paper",
    identifiedResourceName = "EpisodClear20",
    identifiedDescriptionName = {
      "Chapter 2 native enchant material (Ch2_Kindle_Hal_Y).",
      "Type: Etc",
      "Weight: 0.1",
      "^777777Generic compatibility icon; server label.^000000"
    },
    slotCount = 0, ClassNum = 0, costume = false
  }
}

-- These eight active monster drops are missing from the supplied base metadata.
-- Keep an independently supplied definition when a later translation adds one.
local missing_drops = {
  [1002678] = {
    unidentifiedDisplayName = "Crispy Yongjirak Meat",
    unidentifiedResourceName = "EpisodClear20",
    unidentifiedDescriptionName = { "" },
    identifiedDisplayName = "Crispy Yongjirak Meat",
    identifiedResourceName = "EpisodClear20",
    identifiedDescriptionName = { "Type: Etc", "Weight: 1" },
    slotCount = 0, ClassNum = 0, costume = false
  },
  [1002679] = {
    unidentifiedDisplayName = "Burning Leather",
    unidentifiedResourceName = "EpisodClear20",
    unidentifiedDescriptionName = { "" },
    identifiedDisplayName = "Burning Leather",
    identifiedResourceName = "EpisodClear20",
    identifiedDescriptionName = { "Type: Etc", "Weight: 1" },
    slotCount = 0, ClassNum = 0, costume = false
  },
  [1002681] = {
    unidentifiedDisplayName = "Old Snack",
    unidentifiedResourceName = "EpisodClear20",
    unidentifiedDescriptionName = { "" },
    identifiedDisplayName = "Old Snack",
    identifiedResourceName = "EpisodClear20",
    identifiedDescriptionName = { "Type: Etc", "Weight: 1" },
    slotCount = 0, ClassNum = 0, costume = false
  },
  [1002683] = {
    unidentifiedDisplayName = "Fluffy Sparks",
    unidentifiedResourceName = "EpisodClear20",
    unidentifiedDescriptionName = { "" },
    identifiedDisplayName = "Fluffy Sparks",
    identifiedResourceName = "EpisodClear20",
    identifiedDescriptionName = { "Type: Etc", "Weight: 1" },
    slotCount = 0, ClassNum = 0, costume = false
  },
  [1002693] = {
    unidentifiedDisplayName = "Frost Shards",
    unidentifiedResourceName = "EpisodClear20",
    unidentifiedDescriptionName = { "" },
    identifiedDisplayName = "Frost Shards",
    identifiedResourceName = "EpisodClear20",
    identifiedDescriptionName = { "Type: Etc", "Weight: 1" },
    slotCount = 0, ClassNum = 0, costume = false
  },
  [1002695] = {
    unidentifiedDisplayName = "Ice Jelly",
    unidentifiedResourceName = "EpisodClear20",
    unidentifiedDescriptionName = { "" },
    identifiedDisplayName = "Ice Jelly",
    identifiedResourceName = "EpisodClear20",
    identifiedDescriptionName = { "Type: Etc", "Weight: 1" },
    slotCount = 0, ClassNum = 0, costume = false
  },
  [1002702] = {
    unidentifiedDisplayName = "Ghost Flower",
    unidentifiedResourceName = "EpisodClear20",
    unidentifiedDescriptionName = { "" },
    identifiedDisplayName = "Ghost Flower",
    identifiedResourceName = "EpisodClear20",
    identifiedDescriptionName = { "Type: Etc", "Weight: 0" },
    slotCount = 0, ClassNum = 0, costume = false
  },
  [1002705] = {
    unidentifiedDisplayName = "Halppeong",
    unidentifiedResourceName = "EpisodClear20",
    unidentifiedDescriptionName = { "" },
    identifiedDisplayName = "Halppeong",
    identifiedResourceName = "EpisodClear20",
    identifiedDescriptionName = { "Type: Etc", "Weight: 0" },
    slotCount = 0, ClassNum = 0, costume = false
  }
}
for id, record in pairs(missing_drops) do
  if not tbl or not tbl[id] then tbl_chapter2materials[id] = record end
end
