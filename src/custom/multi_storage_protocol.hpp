// Internal map/character protocol; never accepted from a game client.
// PN contributions: GPL-3.0-or-later.
#ifndef PN_MULTI_STORAGE_PROTOCOL_HPP
#define PN_MULTI_STORAGE_PROTOCOL_HPP
#include <common/mmo.hpp>
#include "multi_storage.hpp"
#pragma pack(push, 1)
struct pn_storage_request {
    uint16_t packet = 0x308f, length = sizeof(pn_storage_request);
    uint32_t account_id = 0, char_id = 0;
    uint64_t nonce_hi = 0, nonce_lo = 0, sequence = 0;
    uint8_t page = 0, action = 0;
    uint16_t reserved = 0;
    int64_t wallet_before = 0, wallet_after = 0;
};
struct pn_storage_reply {
    uint16_t packet = 0x388f, length = sizeof(pn_storage_reply);
    uint32_t account_id = 0, char_id = 0;
    uint64_t nonce_hi = 0, nonce_lo = 0, sequence = 0;
    uint8_t page = 0, success = 0;
};
#pragma pack(pop)
static_assert(sizeof(pn_storage_request) == 56, "Storage request ABI");
static_assert(sizeof(pn_storage_reply) == 38, "Storage reply ABI");
static_assert(sizeof(pn_storage_request) + (MAX_INVENTORY + MAX_STORAGE) * sizeof(item) < UINT16_MAX,
    "Atomic inventory/storage packet exceeds the internal protocol frame");
static_assert(sizeof(pn_storage_request) + (MAX_CART + MAX_STORAGE) * sizeof(item) < UINT16_MAX,
    "Atomic cart/storage packet exceeds the internal protocol frame");
#endif
