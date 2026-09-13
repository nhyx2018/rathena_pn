// PN account bank. GPL-3.0-or-later. Shared by the server and Windows client.
#ifndef PN_BANK_PROTOCOL_HPP
#define PN_BANK_PROTOCOL_HPP
#include <cstdint>
#include <algorithm>
#include <limits>

namespace pn_bank {
constexpr uint32_t magic = 0x314b4250; // PBK1, on a separate authenticated socket.
constexpr uint16_t version = 2;
constexpr int64_t bank_limit = INT64_MAX;
constexpr int64_t wallet_limit = INT32_MAX;
constexpr uint32_t open_panel = 1;
constexpr uint32_t item_ids[2] = {6024, 12781};
constexpr uint32_t buy_prices[2] = {501000000, 1002000};
constexpr uint32_t sell_prices[2] = {499000000, 998000};
enum Action : uint32_t { Refresh, Deposit, Withdraw, BuyDiamond, SellDiamond, BuyNote, SellNote };
enum Result : uint32_t { Ok, Saving, Unauthorized, Invalid, Busy, Unavailable, Funds, Capacity, Limit, Items, Stale, SaveFailed };
#pragma pack(push, 1)
struct alignas(8) Request {
    uint32_t magic_value = magic;
    uint16_t protocol = version, length = 64;
    uint32_t account_id = 0, char_id = 0, login_id1 = 0, login_id2 = 0;
    uint64_t nonce_hi = 0, nonce_lo = 0, request_id = 0;
    int64_t amount = 0;
    uint32_t action = Refresh, reserved = 0;
};
struct alignas(8) Reply {
    uint32_t magic_value = magic;
    uint16_t protocol = version, length = 136;
    uint64_t nonce_hi = 0, nonce_lo = 0, request_id = 0;
    uint32_t result = Unauthorized, flags = 0;
    int64_t bank = 0, wallet = 0, bank_limit = pn_bank::bank_limit, wallet_limit = pn_bank::wallet_limit;
    uint32_t counts[2] = {}, buy[2] = {buy_prices[0], buy_prices[1]}, sell[2] = {sell_prices[0], sell_prices[1]};
    uint32_t max_buy[2] = {}, max_sell[2] = {};
    int64_t max_deposit = 0, max_withdraw = 0;
    uint32_t char_id = 0, reserved = 0;
};
#pragma pack(pop)
static_assert(sizeof(Request) == 64, "Bank request ABI");
static_assert(sizeof(Reply) == 136, "Bank reply ABI");

inline bool valid_reply(const Reply& state) {
    if (state.magic_value != magic || state.protocol != version || state.length != sizeof(Reply) ||
        (state.flags & ~open_panel) || state.reserved || state.result > SaveFailed ||
        state.bank_limit != bank_limit || state.wallet_limit != wallet_limit ||
        state.bank < 0 || state.wallet < 0 || state.wallet > wallet_limit ||
        state.max_deposit < 0 || state.max_deposit > std::min(state.wallet, bank_limit - state.bank) ||
        state.max_withdraw < 0 || state.max_withdraw > std::min(state.bank, wallet_limit - state.wallet)) return false;
    for (int i = 0; i < 2; ++i)
        if (state.buy[i] != buy_prices[i] || state.sell[i] != sell_prices[i] ||
            state.max_buy[i] > static_cast<uint64_t>(state.bank / buy_prices[i]) ||
            state.max_sell[i] > state.counts[i] ||
            state.max_sell[i] > static_cast<uint64_t>((bank_limit - state.bank) / sell_prices[i])) return false;
    return true;
}

struct Plan {
    Result result = Invalid;
    int64_t bank = 0, wallet = 0;
    int item = -1;
    int32_t item_delta = 0;
};

// All arithmetic is checked before any inventory, wallet, or SQL mutation.
inline Plan plan(const Reply& state, uint32_t action, int64_t amount) {
    Plan out; out.bank = state.bank; out.wallet = state.wallet;
    if (state.bank < 0 || state.wallet < 0 || state.wallet > wallet_limit || amount <= 0)
        return out;
    if (action == Deposit) {
        if (amount > state.wallet) { out.result = Funds; return out; }
        if (amount > bank_limit - state.bank) { out.result = Limit; return out; }
        out.bank += amount; out.wallet -= amount;
    } else if (action == Withdraw) {
        if (amount > state.bank) { out.result = Funds; return out; }
        if (amount > wallet_limit - state.wallet) { out.result = Limit; return out; }
        out.bank -= amount; out.wallet += amount;
    } else if (action >= BuyDiamond && action <= SellNote) {
        out.item = (action - BuyDiamond) / 2;
        bool buy = (action == BuyDiamond || action == BuyNote);
        uint32_t price = buy ? buy_prices[out.item] : sell_prices[out.item];
        if (amount > INT32_MAX || amount > bank_limit / price) { out.result = Limit; return out; }
        int64_t total = amount * price;
        if (buy) {
            if (total > state.bank) { out.result = Funds; return out; }
            if (amount > state.max_buy[out.item]) { out.result = Capacity; return out; }
            out.bank -= total; out.item_delta = static_cast<int32_t>(amount);
        } else {
            if (amount > state.counts[out.item]) { out.result = Items; return out; }
            if (total > bank_limit - state.bank) { out.result = Limit; return out; }
            out.bank += total; out.item_delta = -static_cast<int32_t>(amount);
        }
    } else return out;
    out.result = Ok;
    return out;
}
inline const char* message(uint32_t result) {
    switch (result) {
    case Ok: return "Choose a banking action.";
    case Saving: return "Saving transaction. Please wait...";
    case Unauthorized: return "Log in to a character to use the bank.";
    case Invalid: return "Enter a valid whole amount greater than zero.";
    case Busy: return "Finish your current trade, shop, or NPC dialog first.";
    case Unavailable: return "Banking is unavailable here. Please try again later.";
    case Funds: return "You do not have enough zeny for this action.";
    case Capacity: return "There is not enough inventory space or weight capacity.";
    case Limit: return "This amount would exceed the wallet or bank limit.";
    case Items: return "You do not have enough eligible items to sell.";
    case Stale: return "Your session changed. Refresh before trying again.";
    default: return "The transaction is waiting for the character server to save.";
    }
}
}
#endif
