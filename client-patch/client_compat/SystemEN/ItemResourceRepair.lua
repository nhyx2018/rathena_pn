-- Repair only the reviewed missing unidentified-helmet resource references.
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
