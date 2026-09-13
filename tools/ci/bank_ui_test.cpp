// Exercise real Windows edit/button controls and the production panel handlers.
// Only the authenticated transport is replaced; no player data is touched.
#define PN_BANK_UI_TEST
#include "../../client-patch/account_bank/bank_ui.cpp"
#include <iostream>

namespace fixture {
struct Request { uint32_t action; int64_t amount; uint64_t sequence; };
std::vector<Request> requests;
bool authenticated=true, connected=true;
LONG generation=7;
}
void bank_install_transport(HWND) {}
bool bank_authenticated() { return fixture::authenticated; }
bool bank_current_generation(LONG value,bool active) {
    return value==fixture::generation && (!active || fixture::authenticated);
}
bool bank_connection_ready() { return fixture::connected; }
HWND bank_find_game_window() { return nullptr; }
bool bank_submit(HWND,const pn_bank::Reply&,uint32_t action,int64_t value,uint64_t id) {
    if(!fixture::authenticated || !fixture::connected) return false;
    fixture::requests.push_back({action,value,id});return true;
}
static void reply(pn_bank::Reply value,bool connected=true,LONG generation=fixture::generation) {
    assert(pn_bank::valid_reply(value));
    SendMessage(panel,BANK_RESULT,0,reinterpret_cast<LPARAM>(new BankResult{value,generation,connected}));
}
static pn_bank::Reply funded() {
    pn_bank::Reply value;value.result=pn_bank::Ok;value.bank=2000000000;value.wallet=1000000;
    value.max_deposit=value.wallet;value.max_withdraw=value.bank;
    for(int i=0;i<2;++i) {
        value.counts[i]=10;value.max_sell[i]=10;value.max_buy[i]=value.bank/value.buy[i];
    }
    return value;
}
static void click(int id) { SendMessage(GetDlgItem(panel,id),BM_CLICK,0,0); }
int main() {
    instance=GetModuleHandle(nullptr);
    WNDCLASSW type{};type.lpfnWndProc=window_proc;type.hInstance=instance;type.lpszClassName=L"PNBankUIFixture";
    assert(RegisterClassW(&type));
    panel=CreateWindowExW(WS_EX_TOOLWINDOW,type.lpszClassName,L"",WS_POPUP,0,0,522,642,nullptr,nullptr,instance,nullptr);
    assert(panel);
    // These fail in the reported build: both item edits originally started at 0.
    assert(amount(0)==0 && amount(1)==1 && amount(2)==1);
    update();for(auto control:actions) assert(!IsWindowEnabled(control));
    auto value=funded();reply(value);
    for(int i=2;i<6;++i) assert(IsWindowEnabled(actions[i]));
    for(int row=1;row<3;++row) for(bool buy:{true,false}) assert(exchange_block_reason(row,buy).empty());
    for(int id=402;id<=405;++id) {
        reply(value);const auto before=fixture::requests.size();click(id);
        assert(fixture::requests.size()==before+1);
        const auto request=fixture::requests.back();
        assert(request.action==static_cast<uint32_t>(id-399) && request.amount==1 && request.sequence>0);
        for(auto control:actions) assert(!IsWindowEnabled(control));
        click(id);SendMessage(panel,WM_COMMAND,id,0);
        assert(fixture::requests.size()==before+1); // no duplicate while saving
        auto pending=value;pending.result=pn_bank::Saving;reply(pending);
        click(id);SendMessage(panel,WM_COMMAND,id,0);assert(fixture::requests.size()==before+1);
        value.request_id=request.sequence;reply(value);
    }
    for(int row=1;row<3;++row) {
        for(auto invalid:{L"0",L"",L"-1",L"1.5",L"9223372036854775808"}) {
            SetWindowTextW(inputs[row],invalid);
            const auto before=fixture::requests.size();
            assert(!IsWindowEnabled(actions[row*2]) && !IsWindowEnabled(actions[row*2+1]));
            click(400+row*2);click(401+row*2);
            assert(fixture::requests.size()==before);
        }
        set_amount(row,0);click(500+row*10);assert(amount(row)==1);
        assert(IsWindowEnabled(actions[row*2]) && IsWindowEnabled(actions[row*2+1]));
    }
    // Each genuine restriction still disables the appropriate action.
    auto empty=value;empty.bank=0;empty.max_withdraw=0;
    for(int i=0;i<2;++i) empty.max_buy[i]=0;
    reply(empty);
    assert(!IsWindowEnabled(actions[2]) && !IsWindowEnabled(actions[4]));
    assert(IsWindowEnabled(actions[3]) && IsWindowEnabled(actions[5]));
    assert(exchange_block_reason(1,true).find(L"501,000,000 more Zeny")!=std::wstring::npos);
    assert(exchange_block_reason(2,true).find(L"1,002,000 more Zeny")!=std::wstring::npos);
    empty=value;
    for(int i=0;i<2;++i) empty.counts[i]=empty.max_sell[i]=0;
    reply(empty);
    assert(IsWindowEnabled(actions[2]) && IsWindowEnabled(actions[4]));
    assert(!IsWindowEnabled(actions[3]) && !IsWindowEnabled(actions[5]));
    assert(exchange_block_reason(1,false).find(L"No eligible items")!=std::wstring::npos);
    empty=value;for(int i=0;i<2;++i) empty.max_buy[i]=0;reply(empty);
    assert(!IsWindowEnabled(actions[2]) && !IsWindowEnabled(actions[4]));
    auto full=value;full.bank=INT64_MAX;full.max_deposit=0;
    for(int i=0;i<2;++i) full.max_sell[i]=0;
    reply(full);assert(!IsWindowEnabled(actions[3]) && !IsWindowEnabled(actions[5]));
    assert(exchange_block_reason(2,false).find(L"limit")!=std::wstring::npos);
    // Reproduce the reported state: on-hand funds do not pay for bank purchases.
    auto unfunded=value;unfunded.bank=1000000;unfunded.wallet=1000000000;
    unfunded.max_deposit=unfunded.wallet;unfunded.max_withdraw=unfunded.bank;
    for(int i=0;i<2;++i) unfunded.counts[i]=unfunded.max_buy[i]=unfunded.max_sell[i]=0;
    reply(unfunded);
    for(int i=2;i<6;++i) assert(!IsWindowEnabled(actions[i]));
    assert(exchange_block_reason(1,true)==L"Buy: Deposit 500,000,000 more Zeny into the bank.");
    assert(exchange_block_reason(2,true)==L"Buy: Deposit 2,000 more Zeny into the bank.");
    set_amount(0,2000);click(400);
    assert(fixture::requests.back().action==pn_bank::Deposit && fixture::requests.back().amount==2000);
    unfunded.bank+=2000;unfunded.wallet-=2000;unfunded.max_deposit=unfunded.wallet;unfunded.max_withdraw=unfunded.bank;
    unfunded.max_buy[1]=1;reply(unfunded);
    assert(!IsWindowEnabled(actions[2]) && IsWindowEnabled(actions[4]));
    assert(exchange_block_reason(2,true).empty());
    click(404);assert(fixture::requests.back().action==pn_bank::BuyNote && fixture::requests.back().amount==1);
    unfunded.bank-=1002000;unfunded.max_withdraw=unfunded.bank;unfunded.max_buy[1]=0;
    unfunded.counts[1]=unfunded.max_sell[1]=1;reply(unfunded);
    assert(IsWindowEnabled(actions[5]) && exchange_block_reason(2,false).empty());
    click(405);assert(fixture::requests.back().action==pn_bank::SellNote && fixture::requests.back().amount==1);
    for(auto result:{pn_bank::Unavailable,pn_bank::Saving,pn_bank::Unauthorized}) {
        auto blocked=value;blocked.result=result;reply(blocked);
        const auto before=fixture::requests.size();
        for(int id=400;id<406;++id) { click(id);SendMessage(panel,WM_COMMAND,id,0); }
        assert(fixture::requests.size()==before);
    }
    reply(value);reply(value,false);
    for(auto control:actions) assert(!IsWindowEnabled(control));
    reply(value);set_amount(1,10);set_amount(2,100);
    fixture::authenticated=false;++fixture::generation;
    SendMessage(panel,BANK_SESSION,fixture::generation,0);
    assert(amount(0)==0 && amount(1)==1 && amount(2)==1);
    reply(value,true,fixture::generation-1);
    for(auto control:actions) assert(!IsWindowEnabled(control));
    DestroyWindow(panel);
    std::cout<<"PASS: default item quantities; all four native Buy/Sell clicks; pending/duplicate guards; zero/invalid input; presets; visible rejection reasons; deposit then buy/sell control recovery; funds, eligible items, inventory and bank capacity; unavailable, disconnected and stale sessions\n";
}
