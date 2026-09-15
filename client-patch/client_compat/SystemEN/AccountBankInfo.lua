-- PN account-bank metadata. The translated base omits item 12781 entirely.
-- Define it before applying descriptions so the client can register the ticket.
-- Reuse the existing coupon artwork (CP949 bytes); no new GRF is required.
-- Preserve resource identifiers when an installation already defines the item.
if not tbl[12781] then
    tbl[12781] = {
        unidentifiedResourceName = "\196\237\198\249",
        unidentifiedDescriptionName = { "" },
        identifiedResourceName = "\196\237\198\249",
        slotCount = 0,
        ClassNum = 0,
        costume = false,
        Custom = true
    }
end

local descriptions = {
    [6024] = {
        "A valuable diamond that can be exchanged at the Account Bank.",
        "^0000FFBank buy price:^000000 501,000,000 zeny",
        "^0000FFBank sell price:^000000 499,000,000 zeny",
        "Use ^0000FF@bank^000000 or ^0000FFAlt+B^000000 to open the bank.",
        "Favorite, bound, modified and rental items cannot be exchanged."
    },
    [12781] = {
        "A 1M Zeny Ticket item that can be exchanged at the Account Bank.",
        "^0000FFBank buy price:^000000 1,002,000 zeny",
        "^0000FFBank sell price:^000000 998,000 zeny",
        "Use ^0000FF@bank^000000 or ^0000FFAlt+B^000000 to open the bank.",
        "Favorite, bound, modified and rental items cannot be exchanged.",
        "^0000CCWeight:^000000 0"
    }
}
for id, lines in pairs(descriptions) do
    if tbl[id] then tbl[id].identifiedDescriptionName = lines end
end
tbl[12781].identifiedDisplayName = "1M Zeny Ticket"
tbl[12781].unidentifiedDisplayName = "1M Zeny Ticket"
