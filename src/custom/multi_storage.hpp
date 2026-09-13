// PN multi-storage. GPL-3.0-or-later.
#ifndef PN_MULTI_STORAGE_HPP
#define PN_MULTI_STORAGE_HPP
#include <cstdint>
#include <cstring>
namespace pn_storage {
constexpr int64_t expansion_price = 50000000;
constexpr uint8_t regular_first = 100, regular_last = 108;
constexpr uint8_t master_first = 110, master_last = 115;
constexpr uint8_t cards = 116, character = 117;
constexpr const char* paid_key = "#PNStoragePaid";
constexpr const char* name_key = "#PNStorageName$";
inline bool managed(int id) {
    return id == 0 || (id >= regular_first && id <= regular_last) ||
        (id >= master_first && id <= character);
}
inline bool free_page(int id) {
    return id == 0 || id == 100 || id == 101 || id == master_first || id == cards || id == character;
}
inline bool purchasable(int id) { return managed(id) && !free_page(id); }
inline bool valid_name(const char* value) {
    size_t length = value ? strlen(value) : 0;
    if (length == 0 || length > 23 || value[0] == ' ' || value[length-1] == ' ') return false;
    for (const unsigned char* p = reinterpret_cast<const unsigned char*>(value); *p; ++p)
        if (*p < 32 || *p > 126 || *p == ':' || *p == '^') return false;
    return true;
}
enum Action : uint8_t { Inventory = 1, Cart = 2, Unlock = 3 };
struct State {
    uint64_t nonce_hi = 0, nonce_lo = 0, sequence = 0;
    int64_t wallet_before = 0;
    uint8_t page = 0, action = 0, mode = 0;
    bool pending = false, applying = false, loading = false;
};
}
#endif
