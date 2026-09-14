-- Repair only reviewed resource-name typos; preserve independently corrected art.
-- Decimal escapes retain the client's CP949 bytes in an ASCII source file.
local missing = "\197\245\177\184"
local helmet = "\199\239\184\167"
local ids = {5581, 5582}
for id = 400529, 400546 do ids[#ids + 1] = id end
for _, id in ipairs(ids) do
    local entry = tbl[id]
    if entry and entry.unidentifiedResourceName == missing then
        entry.unidentifiedResourceName = helmet
    end
end

-- Assassin Mask uses the installed artwork shared with item 5096.
-- Silvervine Fruit and Coconut Juice use their own identified artwork.
local repairs = {
	{5054, "identifiedResourceName", "\190\238\188\188\189\197\184\182\189\186\197\169", "\190\238\187\245\189\197\184\182\189\186\197\169"},
	{6417, "unidentifiedResourceName", "\176\179\180\217\191\173\184\197", "\176\179\180\217\183\161\191\173\184\197"},
	{11534, "unidentifiedResourceName", "\190\198\192\218\193\234\189\186", "\190\223\192\218\193\234\189\186"},
}
for _, repair in ipairs(repairs) do
    local entry = tbl[repair[1]]
    if entry and entry[repair[2]] == repair[3] then
        entry[repair[2]] = repair[4]
    end
end
