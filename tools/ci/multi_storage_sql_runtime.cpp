// Link the real character-server SQL implementation; disposable fixture only.
#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <string>
#include "char/char.hpp"
#include "char/inter.hpp"
#include "char/int_storage.hpp"
#include "common/malloc.hpp"
#include "common/sql.hpp"
#include "common/timer.hpp"
#include "custom/multi_storage_protocol.hpp"

bool personal_storage_tosql(const pn_storage_request&, const item*, const item*);
bool inventory_fromsql(uint32, s_storage*);
bool storage_fromsql(uint32, s_storage*);
extern std::string cfgFile;
static int checks = 0;
static void sql(const std::string& query) { assert(Sql_QueryStr(sql_handle, query.c_str()) == SQL_SUCCESS); }
static std::string result(const std::string& query) {
    sql(query); std::string value; int code;
    while ((code = Sql_NextRow(sql_handle)) == SQL_SUCCESS) {
        for (unsigned i = 0; i < Sql_NumColumns(sql_handle); ++i) {
            char* data = nullptr; size_t length = 0;
            assert(Sql_GetData(sql_handle, i, &data, &length) == SQL_SUCCESS);
            value += data ? std::string(data, length) : "NULL"; value += '|';
        }
        value += '\n';
    }
    assert(code == SQL_NO_DATA); Sql_FreeResult(sql_handle); return value;
}
static std::string snapshot() {
    std::string value = result("SELECT char_id,account_id,zeny FROM `char` ORDER BY char_id") +
        result("SELECT * FROM acc_reg_num ORDER BY account_id,`key`,`index`") +
        result("SELECT * FROM inventory ORDER BY id") + result("SELECT * FROM cart_inventory ORDER BY id") +
        result("SELECT * FROM pn_storage_commits ORDER BY account_id,nonce_hi,nonce_lo,request_id");
    for (const auto& entry : interServerDb)
        value += result(std::string("SELECT * FROM `") + entry.second->table + "` ORDER BY id");
    return value;
}
static void unchanged(const std::string& before) { assert(snapshot() == before); ++checks; }
static void connect_db() {
    sql_handle = Sql_Malloc();
    assert(Sql_Connect(sql_handle, "root", "storage-validation-only", "storage-20260913-db", 3306, "storage_probe") == SQL_SUCCESS);
    assert(result("SELECT DATABASE()") == "storage_probe|\n");
    strcpy(schema_config.inventory_db, "inventory"); strcpy(schema_config.cart_db, "cart_inventory");
    strcpy(schema_config.char_db, "char"); strcpy(schema_config.acc_reg_num_table, "acc_reg_num");
}
extern "C" int __wrap_main(int argc, char** argv) {
    malloc_init(); timer_init(); connect_db(); cfgFile = "inter_server.yml"; interServerDb.load();
    assert(interServerDb.size() == 18);
    sql("DELETE FROM pn_storage_commits"); sql("DELETE FROM inventory"); sql("DELETE FROM cart_inventory");
    sql("DELETE FROM acc_reg_num"); sql("DELETE FROM `char`");
    for (const auto& entry : interServerDb) sql(std::string("DELETE FROM `") + entry.second->table + '`');
    sql("INSERT INTO `char` (char_id,account_id,zeny,name) VALUES (99001313,990013,2000000000,'Storage fixture'),(99001314,990013,100000000,'Sibling fixture'),(99001315,990014,1,'Other account')");
    sql("INSERT INTO inventory(id,char_id,nameid,amount,identify,refine,bound,unique_id,card0,option_id0,option_val0,option_parm0,enchantgrade) VALUES (1,99001313,501,2,1,0,0,0,0,0,0,0,0),(2,99001313,1201,1,1,10,2,987654321,4001,1,27,3,4)");
    s_storage source{}, page{}; assert(inventory_fromsql(99001313, &source));
    page.u.items_storage[0] = source.u.items_inventory[0]; page.u.items_storage[0].amount = 1;
    source.u.items_inventory[0].amount = 1;
    page.u.items_storage[1] = source.u.items_inventory[1]; source.u.items_inventory[1] = {};
    pn_storage_request request;
    request.account_id = 990013; request.char_id = 99001313;
    request.nonce_hi = 111; request.nonce_lo = 222; request.sequence = 1;
    request.page = 100; request.action = pn_storage::Inventory;
    request.wallet_before = request.wallet_after = 2000000000;
    auto cached = std::make_shared<mmo_charstatus>(); cached->zeny = 2000000000;
    char_get_chardb()[request.char_id] = cached;
    auto original = snapshot();
    if (argc > 1 && std::string(argv[1]) == "crash") {
        sql("CREATE TRIGGER storage_crash BEFORE INSERT ON pn_storage_commits FOR EACH ROW DO SLEEP(20)");
        std::cout << "CRASH_READY" << std::endl;
        bool committed = personal_storage_tosql(request, source.u.items_inventory, page.u.items_storage);
        std::cout << "CRASH_RETURN " << committed << std::endl; assert(!committed); return 0;
    }
    for (const char* failure : {
        "CREATE TRIGGER storage_fault BEFORE UPDATE ON inventory FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='inventory fault'",
        "CREATE TRIGGER storage_fault BEFORE INSERT ON pn_storage_02 FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='page fault'",
        "CREATE TRIGGER storage_fault BEFORE UPDATE ON `char` FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='wallet fault'",
        "CREATE TRIGGER storage_fault BEFORE INSERT ON pn_storage_commits FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='journal fault'"}) {
        sql(failure); assert(!personal_storage_tosql(request, source.u.items_inventory, page.u.items_storage)); ++checks;
        unchanged(original); assert(cached->zeny == 2000000000); ++checks; sql("DROP TRIGGER storage_fault");
    }
    for (const char* table : {"inventory", "cart_inventory", "char", "acc_reg_num", "pn_storage_02", "pn_storage_commits"}) {
        if (std::string(table) == "cart_inventory") request.action = pn_storage::Cart;
        sql(std::string("ALTER TABLE `") + table + "` ENGINE=MyISAM");
        assert(!personal_storage_tosql(request, source.u.items_storage, page.u.items_storage)); ++checks; unchanged(original);
        sql(std::string("ALTER TABLE `") + table + "` ENGINE=InnoDB"); request.action = pn_storage::Inventory;
    }
    for (int bad = 0; bad < 11; ++bad) {
        auto invalid = request;
        if (bad == 0) invalid.account_id = 990014;
        if (bad == 1) invalid.char_id = 1;
        if (bad == 2) invalid.page = 102; // Locked paid page.
        if (bad == 3) invalid.page = 109; // Unconfigured gap.
        if (bad == 4) invalid.wallet_after = int64_t(MAX_ZENY) + 1;
        if (bad == 5) invalid.wallet_after = -1;
        if (bad == 6) invalid.sequence = 0;
        if (bad == 7) invalid.nonce_hi = invalid.nonce_lo = 0;
        if (bad == 8) invalid.action = 4;
        if (bad == 9) invalid.reserved = 1;
        if (bad == 10) invalid.wallet_before = -1;
        assert(!personal_storage_tosql(invalid, source.u.items_inventory, page.u.items_storage)); ++checks; unchanged(original);
    }
    assert(personal_storage_tosql(request, source.u.items_inventory, page.u.items_storage)); ++checks;
    assert(result("SELECT SUM(amount) FROM inventory WHERE nameid=501") == "1|\n"); ++checks;
    assert(result("SELECT refine,bound,unique_id,card0,option_id0,option_val0,option_parm0,enchantgrade FROM pn_storage_02 WHERE nameid=1201") == "10|2|987654321|4001|1|27|3|4|\n"); ++checks;
    auto committed = snapshot(); auto saved = request;
    source.u.items_inventory[0].amount = 99; page.u.items_storage[0].amount = 99; request.wallet_after = 7; cached->zeny = 333;
    assert(personal_storage_tosql(request, source.u.items_inventory, page.u.items_storage)); ++checks; unchanged(committed);
    assert(cached->zeny == 333); ++checks;
    Sql_Free(sql_handle); connect_db();
    assert(personal_storage_tosql(request, source.u.items_inventory, page.u.items_storage)); ++checks; unchanged(committed);
    request.page = 101; assert(!personal_storage_tosql(request, source.u.items_inventory, page.u.items_storage)); ++checks; unchanged(committed);
    request = saved; ++request.sequence;
    assert(inventory_fromsql(request.char_id, &source));
    page = {}; page.stor_id = 100; assert(storage_fromsql(request.account_id, &page));
    assert(page.id == request.account_id && page.amount == 2 && page.max_amount == 600); ++checks;
    // Cart and its page commit together, with the inventory left untouched.
    auto inventory_before = result("SELECT * FROM inventory ORDER BY id");
    std::array<item, MAX_CART> cart{}; cart[0] = page.u.items_storage[0];
    page.u.items_storage[0] = {}; request.action = pn_storage::Cart;
    assert(personal_storage_tosql(request, cart.data(), page.u.items_storage)); ++checks;
    assert(result("SELECT amount FROM cart_inventory WHERE char_id=99001313 AND nameid=501") == "1|\n"); ++checks;
    assert(result("SELECT * FROM inventory ORDER BY id") == inventory_before); ++checks;
    // Unlock failure rolls back both the wallet and the entitlement.
    request.action = pn_storage::Unlock; request.page = 102; ++request.sequence;
    request.wallet_after = request.wallet_before - pn_storage::expansion_price; original = snapshot();
    for (const char* table : {"acc_reg_num", "pn_storage_commits"}) {
        sql(std::string("CREATE TRIGGER storage_fault BEFORE INSERT ON `") + table + "` FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='unlock fault'");
        assert(!personal_storage_tosql(request, source.u.items_inventory, nullptr)); ++checks; unchanged(original);
        sql("DROP TRIGGER storage_fault");
    }
    auto poor = request; poor.wallet_before = 49999999; poor.wallet_after = 0;
    assert(!personal_storage_tosql(poor, source.u.items_inventory, nullptr)); ++checks; unchanged(original);
    for (int id = 0; id < 256; ++id) if (pn_storage::purchasable(id)) {
        request.page = id; ++request.sequence;
        assert(personal_storage_tosql(request, source.u.items_inventory, nullptr)); ++checks;
        auto after = snapshot();
        assert(personal_storage_tosql(request, source.u.items_inventory, nullptr)); ++checks; unchanged(after);
        ++request.sequence; assert(!personal_storage_tosql(request, source.u.items_inventory, nullptr)); ++checks; unchanged(after);
        request.wallet_before = request.wallet_after; request.wallet_after -= pn_storage::expansion_price;
    }
    assert(result("SELECT COUNT(*) FROM acc_reg_num WHERE account_id=990013 AND `key`='#PNStoragePaid' AND value=1") == "12|\n"); ++checks;
    assert(result("SELECT zeny FROM `char` WHERE char_id=99001313") == "1400000000|\n"); ++checks;
    // Every configured account page is independent; character storage is keyed by CID.
    request.action = pn_storage::Inventory; request.wallet_before = request.wallet_after = 1400000000;
    for (const auto& entry : interServerDb) {
        request.page = entry.first; ++request.sequence;
        page = {}; page.u.items_storage[0].nameid = 4001; page.u.items_storage[0].amount = 1;
        page.u.items_storage[0].identify = 1; page.u.items_storage[0].bound = request.page == 117 ? BOUND_CHAR : 0;
        page.u.items_storage[0].unique_id = 10000 + request.page;
        assert(personal_storage_tosql(request, source.u.items_inventory, page.u.items_storage)); ++checks;
        s_storage loaded{}; loaded.stor_id = request.page;
        uint32 owner = request.page == 117 ? request.char_id : request.account_id;
        assert(storage_fromsql(owner, &loaded) && loaded.amount == 1 && loaded.u.items_storage[0].unique_id == 10000 + request.page); ++checks;
        loaded = {}; loaded.stor_id = request.page;
        assert(storage_fromsql(request.page == 117 ? 99001314 : 990014, &loaded) && loaded.amount == 0); ++checks;
    }
    request.char_id = 99001314; request.page = 110; ++request.sequence;
    request.wallet_before = request.wallet_after = 100000000;
    source = {}; page = {}; page.stor_id = 110;
    assert(storage_fromsql(request.account_id, &page) && page.amount == 1); ++checks;
    source.u.items_inventory[0] = page.u.items_storage[0]; page.u.items_storage[0] = {};
    assert(personal_storage_tosql(request, source.u.items_inventory, page.u.items_storage)); ++checks;
    assert(result("SELECT unique_id FROM inventory WHERE char_id=99001314") == "10110|\n"); ++checks;
    std::cout << "STORAGE_SQL_PASS " << checks << " checks: atomic transfers/unlocks, rollback, replay, ownership, all pages, character isolation, item metadata and cache synchronization\n";
    Sql_Free(sql_handle); sql_handle = nullptr; return 0;
}
