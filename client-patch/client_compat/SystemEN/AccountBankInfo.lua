-- PN account-bank descriptions. Keep every original icon/resource identifier.
local descriptions = {
    [6024] = {
        "A valuable diamond that can be exchanged at the Account Bank.",
        "^0000FFBank buy price:^000000 501,000,000 zeny",
        "^0000FFBank sell price:^000000 499,000,000 zeny",
        "Use ^0000FF@bank^000000 or ^0000FFAlt+B^000000 to open the bank.",
        "Favorite, bound, modified and rental items cannot be exchanged."
    },
    [12781] = {
        "A zeny note that can be exchanged at the Account Bank.",
        "^0000FFBank buy price:^000000 1,002,000 zeny",
        "^0000FFBank sell price:^000000 998,000 zeny",
        "Use ^0000FF@bank^000000 or ^0000FFAlt+B^000000 to open the bank.",
        "Favorite, bound, modified and rental items cannot be exchanged."
    }
}
for id, lines in pairs(descriptions) do
    if tbl[id] then tbl[id].identifiedDescriptionName = lines end
end
if tbl[12781] then
    tbl[12781].identifiedDisplayName = "1M Zeny"
    tbl[12781].unidentifiedDisplayName = "1M Zeny"
end
