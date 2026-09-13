// Included by map/clif.cpp. The companion socket never owns a player session.
#include <custom/bank_protocol.hpp>

static bool pn_bank_plain_item(const item& entry, uint32_t id) {
    if (entry.nameid != id || entry.amount <= 0 || !entry.identify || entry.bound || entry.expire_time ||
        entry.equip || entry.equipSwitch || entry.refine || entry.attribute || entry.enchantgrade) return false;
    for (auto card : entry.card) if (card) return false;
    for (const auto& option : entry.option) if (option.id || option.value || option.param) return false;
    return true;
}
static uint32_t pn_bank_count(const map_session_data& sd, uint32_t id) {
    uint32_t count = 0;
    for (int i = 0; i < MAX_INVENTORY; ++i)
        if (sd.inventory_data[i] && pn_bank_plain_item(sd.inventory.u.items_inventory[i], id) &&
            !sd.inventory.u.items_inventory[i].favorite)
            count += sd.inventory.u.items_inventory[i].amount;
    return count;
}
static uint32_t pn_bank_buy_capacity(const map_session_data& sd, uint32_t id) {
    auto data = item_db.find(id);
    if (!data || !itemdb_isstackable2(data.get()) || data->flag.guid || data->flag.autoequip) return 0;
    int64_t capacity = data->stack.inventory ? std::min<int64_t>(MAX_AMOUNT, data->stack.amount) : MAX_AMOUNT;
    bool stack = false;
    for (int i = 0; i < MAX_INVENTORY; ++i) {
        const auto& entry = sd.inventory.u.items_inventory[i];
        if (entry.nameid != id || entry.bound || entry.expire_time || entry.unique_id) continue;
        bool cards = false; for (auto card : entry.card) if (card) cards = true;
        if (cards) continue;
        if (i >= sd.status.inventory_slots || !pn_bank_plain_item(entry, id)) return 0;
        capacity -= entry.amount; stack = true; break;
    }
    if (!stack && pc_inventoryblank(&sd) == 0) return 0;
    if (data->weight > 0)
        capacity = std::min<int64_t>(capacity, std::max<int64_t>(0, static_cast<int64_t>(sd.max_weight) - sd.weight) / data->weight);
    return static_cast<uint32_t>(std::max<int64_t>(0, capacity));
}
static pn_bank::Reply pn_bank_snapshot(map_session_data& sd) {
    if (!sd.bank_ui.nonce_hi && !sd.bank_ui.nonce_lo) {
        sd.bank_ui.nonce_hi = (static_cast<uint64>(rnd()) << 32) | static_cast<uint32>(rnd());
        sd.bank_ui.nonce_lo = (static_cast<uint64>(rnd()) << 32) | static_cast<uint32>(rnd());
        if (!sd.bank_ui.nonce_hi && !sd.bank_ui.nonce_lo) sd.bank_ui.nonce_lo = 1;
    }
    pn_bank::Reply result;
    result.char_id = sd.status.char_id;
    result.nonce_hi = sd.bank_ui.nonce_hi; result.nonce_lo = sd.bank_ui.nonce_lo;
    result.char_id = sd.status.char_id; result.request_id = sd.bank_ui.request_id;
    result.bank = sd.bank_vault; result.wallet = sd.status.zeny;
    result.result = sd.bank_ui.pending ? pn_bank::Saving : sd.bank_ui.result;
    if (!battle_config.feature_banking || map_getmapflag(sd.m, MF_NOBANK) || !chrif_isconnected())
        result.result = pn_bank::Unavailable;
    if (result.bank < 0 || result.wallet < 0 || result.wallet > pn_bank::wallet_limit) {
        result.result = pn_bank::Unavailable; return result;
    }
    result.max_deposit = std::min(result.wallet, pn_bank::bank_limit - result.bank);
    result.max_withdraw = std::min(result.bank, pn_bank::wallet_limit - result.wallet);
    for (int i = 0; i < 2; ++i) {
        result.counts[i] = pn_bank_count(sd, pn_bank::item_ids[i]);
        result.max_buy[i] = static_cast<uint32_t>(std::min<int64_t>(pn_bank_buy_capacity(sd, pn_bank::item_ids[i]), result.bank / result.buy[i]));
        result.max_sell[i] = static_cast<uint32_t>(std::min<int64_t>(result.counts[i], (pn_bank::bank_limit - result.bank) / result.sell[i]));
    }
    return result;
}
static pn_bank::Result pn_bank_action(map_session_data& sd, const pn_bank::Request& request) {
    if (!request.request_id || request.nonce_hi != sd.bank_ui.nonce_hi || request.nonce_lo != sd.bank_ui.nonce_lo)
        return pn_bank::Stale;
    if (request.request_id <= sd.bank_ui.request_id) {
        if (request.request_id == sd.bank_ui.request_id && request.action == sd.bank_ui.action && request.amount == sd.bank_ui.amount)
            return sd.bank_ui.pending ? pn_bank::Saving : static_cast<pn_bank::Result>(sd.bank_ui.result);
        return pn_bank::Stale;
    }
    if (sd.bank_ui.pending) return pn_bank::Saving;
    if (!battle_config.feature_banking || map_getmapflag(sd.m, MF_NOBANK) || !chrif_isconnected()) return pn_bank::Unavailable;
    if (pc_isdead(&sd) || pc_cant_act(&sd) || sd.state.autotrade || sd.state.warping ||
        sd.state.changemap || gettick() - sd.bank_ui.last_action_tick < 250) return pn_bank::Busy;
    auto snapshot = pn_bank_snapshot(sd);
    auto plan = pn_bank::plan(snapshot, request.action, request.amount);
    if (plan.result != pn_bank::Ok) return plan.result;

    // The map loop is single-threaded. No player input or split financial save
    // may escape between mutation and the character server's atomic commit.
    s_storage inventory_before = sd.inventory;
    auto weight_before = sd.weight;
    auto& state = sd.bank_ui;
    state.pending = state.applying = true;
    state.bank_before = sd.bank_vault; state.wallet_before = sd.status.zeny;
    if (plan.item_delta > 0) {
        item entry = {}; entry.nameid = pn_bank::item_ids[plan.item]; entry.identify = 1;
        if (pc_additem(&sd, &entry, plan.item_delta, LOG_TYPE_BANK) != ADDITEM_SUCCESS) {
            state.pending = state.applying = false; return pn_bank::Capacity;
        }
    } else if (plan.item_delta < 0) {
        int remaining = -plan.item_delta;
        for (int i = 0; i < MAX_INVENTORY && remaining; ++i) {
            const auto& entry = sd.inventory.u.items_inventory[i];
            if (!sd.inventory_data[i] || !pn_bank_plain_item(entry, pn_bank::item_ids[plan.item]) || entry.favorite) continue;
            int count = std::min<int>(remaining, entry.amount);
            // All native deletion preconditions were checked above. No script
            // callback or event-loop yield occurs in this batch.
            if (pc_delitem(&sd, i, count, 0, 0, LOG_TYPE_BANK) != 0) {
                sd.inventory = inventory_before; sd.weight = weight_before;
                state.pending = state.applying = false;
                pc_setinventorydata(sd); clif_inventorylist(&sd); clif_updatestatus(sd, SP_WEIGHT);
                ShowError("Bank inventory preconditions changed; the local batch was restored.\n");
                return pn_bank::SaveFailed;
            }
            remaining -= count;
        }
    }
    if (plan.wallet < sd.status.zeny) pc_payzeny(&sd, static_cast<int32>(sd.status.zeny - plan.wallet), LOG_TYPE_BANK);
    else if (plan.wallet > sd.status.zeny) pc_getzeny(&sd, static_cast<int32>(plan.wallet - sd.status.zeny), LOG_TYPE_BANK);
    pc_setparam(&sd, SP_BANK_VAULT, plan.bank);
    state.request_id = request.request_id; state.action = request.action; state.amount = request.amount;
    state.native_action = 0;
    state.result = pn_bank::Saving; state.applying = false; state.last_action_tick = gettick();
    intif_bank_save(sd);
    return pn_bank::Saving;
}

int32 clif_bank_native_transfer(map_session_data& sd, int32 amount, bool deposit) {
    auto snapshot = pn_bank_snapshot(sd);
    pn_bank::Request request;
    request.nonce_hi = snapshot.nonce_hi; request.nonce_lo = snapshot.nonce_lo;
    request.request_id = sd.bank_ui.request_id + 1;
    request.action = deposit ? pn_bank::Deposit : pn_bank::Withdraw;
    request.amount = amount;
    auto result = pn_bank_action(sd, request);
    if (result == pn_bank::Saving) sd.bank_ui.native_action = deposit ? 1 : 2;
    return result;
}

// Called before game packet obfuscation, only on an unauthenticated companion
// connection. Its credentials must match an already authenticated live player.
static int32 clif_parse_bank_companion_session(int32 fd);
// A companion owns only this small identity record, never a player pointer.
// delete_session frees it. Validate the nonce as well as fd to prevent reuse
// after logout or character selection from opening another player's panel.
struct pn_bank_companion {
    uint32_t account_id, char_id, login_id1, login_id2;
    uint64_t nonce_hi, nonce_lo;
};
static bool pn_bank_companion_matches(const pn_bank_companion& peer, const map_session_data& sd) {
    return peer.account_id == sd.status.account_id && peer.char_id == sd.status.char_id &&
        peer.login_id1 == sd.login_id1 && peer.login_id2 == sd.login_id2 &&
        peer.nonce_hi == sd.bank_ui.nonce_hi && peer.nonce_lo == sd.bank_ui.nonce_lo;
}
static bool clif_bank_open_custom(map_session_data& sd) {
    sd.bank_ui.open_requested = true;
    int fd = sd.bank_ui.companion_fd;
    if (!session_isValid(fd) || session[fd]->flag.eof ||
        session[fd]->func_parse != clif_parse_bank_companion_session ||
        !session[fd]->session_data || !sd.state.active || !sd.prev ||
        !session_isValid(sd.fd) || session[sd.fd]->flag.eof ||
        session[fd]->client_addr != session[sd.fd]->client_addr ||
        !pn_bank_companion_matches(*static_cast<pn_bank_companion*>(session[fd]->session_data), sd)) return false;
    auto reply = pn_bank_snapshot(sd);
    reply.flags = pn_bank::open_panel;
    WFIFOHEAD(fd, sizeof(reply));
    memcpy(WFIFOP(fd, 0), &reply, sizeof(reply));
    WFIFOSET(fd, sizeof(reply));
    sd.bank_ui.open_requested = false;
    // Also dismiss a stock window opened before the companion authenticated.
    clif_bank_close(sd);
    return true;
}
static bool clif_parse_bank_companion(int32 fd) {
    if (RFIFOW(fd, 0) != (pn_bank::magic & 0xffff)) return false;
    session[fd]->func_parse = clif_parse_bank_companion_session;
    if (RFIFOREST(fd) < sizeof(pn_bank::Request)) return true; // TCP may split the frame.
    pn_bank::Request request;
    memcpy(&request, RFIFOP(fd, 0), sizeof(request));
    RFIFOSKIP(fd, sizeof(request));
    pn_bank::Reply reply;
    if (request.magic_value != pn_bank::magic || request.protocol != pn_bank::version ||
        request.length != sizeof(request) || request.reserved || request.action > pn_bank::SellNote) {
        set_eof(fd); return true;
    }
    auto* sd = map_id2sd(request.account_id);
    bool authenticated = false;
    if (sd && sd->state.active && sd->prev && sd->status.char_id == request.char_id &&
        sd->login_id1 == request.login_id1 && sd->login_id2 == request.login_id2 &&
        session_isValid(sd->fd) && !session[sd->fd]->flag.eof &&
        session[sd->fd]->client_addr == session[fd]->client_addr) {
        reply = pn_bank_snapshot(*sd);
        auto* peer = static_cast<pn_bank_companion*>(session[fd]->session_data);
        if (!peer) {
            peer = static_cast<pn_bank_companion*>(aCalloc(1, sizeof(pn_bank_companion)));
            session[fd]->session_data = peer;
        }
        // Retire the previous attachment before replacing it. A new character
        // or login must authenticate independently, even on a recycled fd.
        if (auto* previous = map_id2sd(peer->account_id))
            if (previous->bank_ui.companion_fd == fd) previous->bank_ui.companion_fd = 0;
        *peer = {request.account_id, request.char_id, request.login_id1, request.login_id2,
            reply.nonce_hi, reply.nonce_lo};
        sd->bank_ui.companion_fd = fd;
        authenticated = true;
        if (request.action != pn_bank::Refresh) {
            auto result = pn_bank_action(*sd, request);
            reply = pn_bank_snapshot(*sd); reply.result = result;
        }
    }
    WFIFOHEAD(fd, sizeof(reply));
    memcpy(WFIFOP(fd, 0), &reply, sizeof(reply));
    WFIFOSET(fd, sizeof(reply));
    // Keep the ordinary request/reply stream separate from open notifications.
    if (authenticated && sd->bank_ui.open_requested) clif_bank_open_custom(*sd);
    return true;
}
static int32 clif_parse_bank_companion_session(int32 fd) {
    if (session[fd]->flag.eof) {
        auto* peer = static_cast<pn_bank_companion*>(session[fd]->session_data);
        if (peer) {
            auto* sd = map_id2sd(peer->account_id);
            if (sd && sd->bank_ui.companion_fd == fd && pn_bank_companion_matches(*peer, *sd))
                sd->bank_ui.companion_fd = 0;
        }
        do_close(fd); return 0;
    }
    if (RFIFOREST(fd) < 2) return 0;
    if (!clif_parse_bank_companion(fd)) set_eof(fd);
    return 0;
}
