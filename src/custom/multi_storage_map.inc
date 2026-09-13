// Included by map/storage.cpp. Native storage windows and server-owned items.
// PN contributions: GPL-3.0-or-later.
bool storage_page_available(map_session_data& sd, int id) {
    if (id < 0 || id > UINT8_MAX || !storage_exists(static_cast<uint8>(id))) return false;
    if (!pn_storage::managed(id) || pn_storage::free_page(id)) return true;
    return pc_readregistry(&sd, reference_uid(add_str(pn_storage::paid_key), id)) == 1;
}

const char* storage_page_name(map_session_data& sd, uint8 id) {
    const char* custom = pc_readregistry_str(&sd, reference_uid(add_str(pn_storage::name_key), id));
    return pn_storage::valid_name(custom) ? custom : storage_getName(id);
}

bool storage_page_rename(map_session_data& sd, int id, const char* name) {
    if (!pn_storage::managed(id) || !storage_exists(id) || pc_transaction_pending(&sd) ||
        sd.multi_storage.loading || (!pn_storage::valid_name(name) && *name)) return false;
    return pc_setregistry_str(&sd, reference_uid(add_str(pn_storage::name_key), id), name);
}

static void storage_session_identity(map_session_data& sd) {
    auto& state = sd.multi_storage;
    if (!state.nonce_hi && !state.nonce_lo) {
        state.nonce_hi = (static_cast<uint64>(rnd()) << 32) | static_cast<uint32>(rnd());
        state.nonce_lo = (static_cast<uint64>(rnd()) << 32) | static_cast<uint32>(rnd());
        if (!state.nonce_hi && !state.nonce_lo) state.nonce_lo = 1;
    }
}

static bool storage_transfer_ready(map_session_data& sd, const s_storage& storage) {
    return !pc_transaction_pending(&sd) && !sd.multi_storage.loading && chrif_isconnected() &&
        storage.type == TABLE_STORAGE && storage_page_available(sd, storage.stor_id) &&
        storage.id == (storage.stor_id == pn_storage::character ? sd.status.char_id : sd.status.account_id);
}

static void storage_commit_transfer(map_session_data& sd, s_storage& storage, bool cart) {
    if (sd.multi_storage.applying) return; // A synchronous @storeall batch commits once.
    storage_session_identity(sd);
    auto& state = sd.multi_storage;
    ++state.sequence;
    state.page = storage.stor_id; state.action = cart ? pn_storage::Cart : pn_storage::Inventory;
    state.wallet_before = sd.status.zeny; state.pending = true;
    intif_storage_commit(sd);
}

void storage_batch_begin(map_session_data& sd) { sd.multi_storage.applying = true; }
void storage_batch_end(map_session_data& sd, s_storage& storage) {
    sd.multi_storage.applying = false;
    if (storage.dirty) storage_commit_transfer(sd, storage, false);
}

bool storage_page_unlock(map_session_data& sd, int id) {
    if (!pn_storage::purchasable(id) || !storage_exists(id) || storage_page_available(sd, id) ||
        pc_cant_act2(&sd) || sd.multi_storage.loading || sd.state.mail_writing || sd.state.autotrade ||
        sd.state.warping || sd.state.changemap || pc_isdead(&sd) || !chrif_isconnected() ||
        sd.status.zeny < pn_storage::expansion_price) return false;
    storage_session_identity(sd);
    auto& state = sd.multi_storage;
    state.wallet_before = sd.status.zeny; state.page = id; state.action = pn_storage::Unlock;
    state.pending = state.applying = true;
    if (pc_payzeny(&sd, pn_storage::expansion_price, LOG_TYPE_OTHER) != 0) {
        state.pending = state.applying = false; return false;
    }
    ++state.sequence;state.applying = false;
    intif_storage_commit(sd);
    return true;
}

static bool storage_request_page(map_session_data& sd, uint8 id, uint8 mode) {
    if (pc_transaction_pending(&sd) || sd.multi_storage.loading || sd.premiumStorage.dirty ||
        !storage_page_available(sd, id) || !chrif_isconnected()) return false;
    storage_session_identity(sd);
    auto& state = sd.multi_storage;
    ++state.sequence;state.page = id;state.mode = mode;state.loading = true;
    if (!intif_storage_page_load(sd)) { state.loading = false; return false; }
    return true;
}
