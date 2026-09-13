// Native owned Windows panel, styled after the owner's supplied reference.
// GPL-3.0-or-later. No embedded browser, account password, or client-side balance authority.
#include "bank_client.hpp"
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <cwchar>
#include <string>
#include <vector>

namespace {
HINSTANCE instance;
HWND panel=nullptr, game=nullptr;
WNDPROC previous_game_proc=nullptr;
HFONT font=nullptr;
HBRUSH white=nullptr;
bool preview=false, busy=false, refreshing=false, verified=false;
uint32_t queued_action=pn_bank::Refresh; // One explicit click may wait for a read-only refresh.
int64_t queued_amount=0;
std::wstring diagnostics_path;
bool last_reply_connected=false;
pn_bank::Reply state;
uint64_t sequence=0;
ULONGLONG last_refresh=0;
std::wstring status=L"Log in to a character to use the bank.";
std::array<HWND,3> inputs{};
std::array<HWND,6> actions{};
constexpr int field_y[3]={117,250,415};
constexpr int preset_y[3]={151,284,449};
constexpr int action_y[3]={103,236,401};
constexpr int edit_ids[3]={100,101,102};
constexpr int refresh_id=200, close_id=201, title_close=202;

bool transaction_pending() { return (busy && !refreshing) || queued_action!=pn_bank::Refresh; }
bool actions_ready() {
    return verified && !transaction_pending() && state.result!=pn_bank::Saving && state.result!=pn_bank::Unavailable;
}

std::wstring wide(const char* value) { return std::wstring(value,value+strlen(value)); }
std::wstring commas(int64_t value,bool zeny=false) {
    std::wstring text=std::to_wstring(value);
    for(int pos=static_cast<int>(text.size())-3;pos>0;pos-=3) text.insert(pos,L",");
    return text+(zeny?L"z":L"");
}
int64_t amount(int row) {
    wchar_t text[64]{}; GetWindowTextW(inputs[row],text,64);
    if(!text[0]) return 0;
    int64_t value=0;
    for(auto p=text;*p;++p) {
        if(*p<L'0' || *p>L'9' || value>(INT64_MAX-(*p-L'0'))/10) return -1;
        value=value*10+(*p-L'0');
    }
    return value;
}
void set_amount(int row,int64_t value) { auto text=std::to_wstring(value); SetWindowTextW(inputs[row],text.c_str()); }
std::wstring exchange_block_reason(int row,bool buy) {
    const std::wstring label=buy?L"Buy: ":L"Sell: ";
    if(!verified) return label+L"Log in, then Refresh to connect to the bank.";
    if(transaction_pending() || state.result==pn_bank::Saving) return label+L"Waiting for the bank. Please wait...";
    if(state.result==pn_bank::Unavailable) return label+L"Banking is unavailable here.";
    const uint32_t action=(row==1?pn_bank::BuyDiamond:pn_bank::BuyNote)+(buy?0:1);
    const auto count=amount(row);
    const auto result=pn_bank::plan(state,action,count).result;
    switch(result) {
    case pn_bank::Ok: return L"";
    case pn_bank::Funds:
        return label+L"Deposit "+commas(count*state.buy[row-1]-state.bank)+L" more Zeny into the bank.";
    case pn_bank::Items:
        return label+(state.counts[row-1]?L"Only "+commas(state.counts[row-1])+L" eligible items on hand.":
            L"No eligible items in your character inventory.");
    case pn_bank::Capacity: return label+L"Free inventory space/weight, or lower the quantity.";
    case pn_bank::Limit: return label+L"Bank balance or transaction limit would be exceeded.";
    default: return label+L"Enter a whole quantity of 1 or more.";
    }
}
void text(HDC dc,int x,int y,int width,const std::wstring& value,bool right=false) {
    RECT box{x,y,x+width,y+20}; DrawTextW(dc,value.c_str(),-1,&box,DT_SINGLELINE|DT_VCENTER|(right?DT_RIGHT:DT_LEFT));
}
void line(HDC dc,int x,int y,int x2,int y2,COLORREF color) {
    auto pen=CreatePen(PS_SOLID,1,color); auto old=SelectObject(dc,pen);
    MoveToEx(dc,x,y,nullptr); LineTo(dc,x2,y2); SelectObject(dc,old); DeleteObject(pen);
}
void gradient(HDC dc,RECT box,COLORREF top,COLORREF bottom) {
    int height=std::max<LONG>(1,box.bottom-box.top);
    for(int i=0;i<height;++i) {
        COLORREF color=RGB(GetRValue(top)+(GetRValue(bottom)-GetRValue(top))*i/height,
            GetGValue(top)+(GetGValue(bottom)-GetGValue(top))*i/height,
            GetBValue(top)+(GetBValue(bottom)-GetBValue(top))*i/height);
        line(dc,box.left,box.top+i,box.right,box.top+i,color);
    }
}
void icon(HDC dc,int row,int x,int y) {
    if(row==1) {
        POINT shape[]={{x+16,y},{x+29,y+10},{x+21,y+29},{x+8,y+29},{x,y+13}};
        auto brush=CreateSolidBrush(RGB(192,191,249)); auto old=SelectObject(dc,brush);
        Polygon(dc,shape,5); SelectObject(dc,old); DeleteObject(brush);
        line(dc,x+16,y,x+9,y+29,RGB(245,247,255)); line(dc,x,y+13,x+29,y+10,RGB(245,247,255));
        line(dc,x+16,y,x+21,y+29,RGB(133,147,220)); line(dc,x+1,y+13,x+21,y+29,RGB(238,238,255));
    } else if(row==2) {
        RECT paper{x+6,y+3,x+25,y+30}; FillRect(dc,&paper,white);
        auto pen=CreatePen(PS_SOLID,2,RGB(193,81,76)); auto old=SelectObject(dc,pen);
        Rectangle(dc,paper.left,paper.top,paper.right,paper.bottom);
        SelectObject(dc,old); DeleteObject(pen);
        SetTextColor(dc,RGB(179,75,67)); text(dc,x+9,y+7,15,L"Z"); SetTextColor(dc,RGB(0,0,0));
        line(dc,x+9,y,x+14,y+5,RGB(140,110,91)); line(dc,x+19,y,x+14,y+5,RGB(140,110,91));
    } else {
        auto brush=CreateSolidBrush(RGB(94,88,145)); auto old=SelectObject(dc,brush);
        Rectangle(dc,x,y+1,x+28,y+22); SelectObject(dc,old); DeleteObject(brush);
        RECT note{x+4,y+5,x+24,y+18}; FillRect(dc,&note,white);
        Ellipse(dc,x+10,y+10,x+33,y+33); text(dc,x+16,y+14,12,L"z");
    }
}
void paint(HDC dc) {
    RECT all{0,0,520,640}; FillRect(dc,&all,white); SelectObject(dc,font);
    SetBkMode(dc,TRANSPARENT); SetTextColor(dc,RGB(0,0,0));
    gradient(dc,RECT{0,0,520,27},RGB(188,200,255),RGB(225,232,255));
    text(dc,12,3,420,L"\x25cf  Bank");
    text(dc,390,3,90,L"v2.2",true);
    text(dc,10,32,495,L"Master Account");
    for(auto range:{std::pair<int,int>{55,181},{185,346},{350,511}}) {
        RECT box{9,range.first,511,range.second}; FrameRect(dc,&box,reinterpret_cast<HBRUSH>(GetStockObject(LTGRAY_BRUSH)));
    }
    text(dc,17,62,160,L"In Bank"); text(dc,182,62,319,commas(state.bank,true),true);
    text(dc,17,80,160,L"On Hand"); text(dc,182,80,319,commas(state.wallet,true),true);
    for(int row=0;row<3;++row) {
        icon(dc,row,17,field_y[row]-2);
        // Paint the edit backing as well, for native WM_PRINT/off-screen renders.
        RECT backing{60,field_y[row],380,field_y[row]+21};
        FillRect(dc,&backing,reinterpret_cast<HBRUSH>(GetStockObject(WHITE_BRUSH)));
        FrameRect(dc,&backing,reinterpret_cast<HBRUSH>(GetStockObject(LTGRAY_BRUSH)));
        wchar_t value[64]{}; GetWindowTextW(inputs[row],value,64);
        text(dc,64,field_y[row],312,value);
    }
    for(int row=1;row<3;++row) {
        int y=row==1?191:356;
        text(dc,17,y,290,row==1?L"17Carat Diamond":L"1M Zeny Ticket");
        text(dc,17,y+21,300,L"On Hand  "+commas(state.counts[row-1]));
        text(dc,345,y,70,L"Buy price"); text(dc,412,y,90,commas(state.buy[row-1],true),true);
        text(dc,345,y+18,70,L"Sell price"); text(dc,412,y+18,90,commas(state.sell[row-1],true),true);
        text(dc,60,field_y[row]-19,347,L"Quantity  (buy up to "+commas(state.max_buy[row-1])+
            L"; sell up to "+commas(state.max_sell[row-1])+L")");
        int64_t count=amount(row);
        bool safe=count>=0 && count<=INT64_MAX/state.buy[row-1];
        int py=row==1?307:472;
        for(int action=0;action<2;++action) {
            const auto reason=exchange_block_reason(row,action==0);
            if(!reason.empty()) {
                SetTextColor(dc,RGB(160,48,34)); text(dc,17,py+action*18,485,reason);
                SetTextColor(dc,RGB(0,0,0));
            } else {
                text(dc,17,py+action*18,290,action==0?L"Zeny paid from bank":L"Zeny added to bank");
                const auto price=action==0?state.buy[row-1]:state.sell[row-1];
                text(dc,307,py+action*18,195,safe?commas(count*price,true):L"Invalid amount",true);
            }
        }
    }
    SetTextColor(dc,RGB(95,95,95));
    text(dc,10,520,500,L"Shared by all characters on this game login.");
    text(dc,10,538,500,L"On-hand limit: "+commas(state.wallet_limit)+L"z");
    text(dc,10,556,500,L"Favorite, bound, modified and rental items cannot be sold.");
    auto guidance=status;
    if(actions_ready() && state.result==pn_bank::Ok && status==wide(pn_bank::message(pn_bank::Ok))) {
        guidance=L"Buy uses bank zeny; Sell uses eligible items on hand.";
        for(int row=1;row<3;++row)
            if(GetFocus()==inputs[row] && amount(row)<=0)
                guidance=L"Enter an item quantity greater than zero to buy or sell.";
    }
    SetTextColor(dc,RGB(0,0,0)); text(dc,10,610,498,guidance);
}
HWND button(int id,const wchar_t* label,int x,int y,int width,int height=21) {
    HWND child=CreateWindowW(L"BUTTON",label,WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_OWNERDRAW,
        x,y,width,height,panel,reinterpret_cast<HMENU>(static_cast<INT_PTR>(id)),instance,nullptr);
    SendMessage(child,WM_SETFONT,reinterpret_cast<WPARAM>(font),TRUE); return child;
}
const char* result_name(uint32_t result) {
    const char* names[]={"Ok","Saving","Unauthorized","Invalid","Busy","Unavailable","Funds","Capacity","Limit","Items","Stale","SaveFailed"};
    return result<=pn_bank::SaveFailed?names[result]:"Unknown";
}
void write_diagnostics(const char* event) {
    if(diagnostics_path.empty()) return;
    FILE* file=_wfopen(diagnostics_path.c_str(),L"w");
    if(!file) return;
    // Local, opt-in latest-state snapshot. Never log identities, balances,
    // inventory counts, login tokens, nonces, raw packets, or passwords.
    std::fprintf(file,"version=2.2\nevent=%s\nuptime_ms=%llu\nauthenticated=%d\nverified=%d\nbusy=%d\nrefreshing=%d\nqueued_action=%u\nlast_reply_connected=%d\nserver_result=%s\n",
        event,static_cast<unsigned long long>(GetTickCount64()),bank_authenticated(),verified,busy,refreshing,queued_action,last_reply_connected,result_name(state.result));
    const char* names[]={"Deposit","Withdraw","BuyDiamond","SellDiamond","BuyTicket","SellTicket"};
    for(int i=0;i<6;++i) {
        const char* reason=!verified?"Unverified":transaction_pending()?"Pending":state.result==pn_bank::Saving?"Saving":
            state.result==pn_bank::Unavailable?"Unavailable":result_name(pn_bank::plan(state,i+1,amount(i/2)).result);
        std::fprintf(file,"%s.enabled=%d\n%s.reason=%s\n",names[i],actions[i] && IsWindowEnabled(actions[i]),names[i],reason);
    }
    std::fclose(file);
}
void configure_diagnostics() {
    wchar_t module[MAX_PATH]{};
    const auto length=GetModuleFileNameW(instance,module,MAX_PATH);
    if(!length || length>=MAX_PATH) return;
    std::wstring directory(module);
    auto slash=directory.find_last_of(L"\\/");
    if(slash==std::wstring::npos) return;
    directory.resize(slash+1);
    if(GetPrivateProfileIntW(L"Bank",L"Diagnostics",0,(directory+L"BankUI.ini").c_str()))
        diagnostics_path=directory+L"BankUI-diagnostics.txt";
}
void enable(HWND control,bool enabled) {
    if(control && !!IsWindowEnabled(control)!=enabled) EnableWindow(control,enabled);
}
void update(const char* event="controls") {
    for(int i=0;i<6;++i) {
        int row=i/2; uint32_t action=i+1;
        auto plan=pn_bank::plan(state,action,amount(row));
        enable(actions[i],actions_ready() && plan.result==pn_bank::Ok);
    }
    enable(GetDlgItem(panel,refresh_id),!transaction_pending());
    InvalidateRect(panel,nullptr,FALSE);
    write_diagnostics(event);
}
void submit(uint32_t action,int64_t value=0) {
    if(preview) return;
    if(action!=pn_bank::Refresh && !actions_ready()) return;
    if(action!=pn_bank::Refresh && pn_bank::plan(state,action,value).result!=pn_bank::Ok) return;
    if(busy) {
        if(action!=pn_bank::Refresh && refreshing) {
            // Keep enabled controls responsive without racing a second worker.
            // Capture the clicked amount and revalidate it against the reply.
            queued_action=action; queued_amount=value;
            status=L"Waiting for the balance check before saving...";
            update("action_queued");
        }
        return;
    }
    uint64_t id=action==pn_bank::Refresh?0:++sequence;
    busy=bank_submit(panel,state,action,value,id);
    refreshing=busy && action==pn_bank::Refresh;
    if(busy) {
        last_refresh=GetTickCount64();
        if(refreshing && verified) { write_diagnostics("refresh_started"); return; }
        status=refreshing?L"Refreshing balances...":L"Saving transaction. Please wait...";
    }
    else { verified=false; status=L"Log in to a character to use the bank."; }
    update("request_started");
}
void show() {
    if(game) SetWindowLongPtr(panel,GWLP_HWNDPARENT,reinterpret_cast<LONG_PTR>(game));
    if(!IsWindowVisible(panel)) {
        RECT area{};
        if(game) GetWindowRect(game,&area); else SystemParametersInfo(SPI_GETWORKAREA,0,&area,0);
        int x=area.left+std::max<LONG>(0,(area.right-area.left-522)/2);
        int y=area.top+std::max<LONG>(0,(area.bottom-area.top-642)/2);
        SetWindowPos(panel,nullptr,x,y,522,642,SWP_NOZORDER);
        ShowWindow(panel,SW_SHOW); SetForegroundWindow(panel); SetFocus(inputs[0]);
    }
    submit(pn_bank::Refresh);
}
LRESULT CALLBACK game_proc(HWND window,UINT message,WPARAM w,LPARAM l) {
    if((message==WM_SYSKEYDOWN || message==WM_KEYDOWN) && w=='B' && ((GetKeyState(VK_MENU)|GetKeyState(VK_CONTROL))&0x8000)) {
        PostMessage(panel,BANK_OPEN,0,0); return 0;
    }
    return CallWindowProc(previous_game_proc,window,message,w,l);
}
void max_menu(int row,HWND source) {
    HMENU menu=CreatePopupMenu();
    AppendMenuW(menu,MF_STRING,1,row==0?L"Maximum deposit":L"Maximum buy");
    AppendMenuW(menu,MF_STRING,2,row==0?L"Maximum withdrawal":L"Maximum sell");
    RECT box; GetWindowRect(source,&box);
    int selected=TrackPopupMenu(menu,TPM_RETURNCMD|TPM_NONOTIFY,box.left,box.bottom,0,panel,nullptr); DestroyMenu(menu);
    if(selected) set_amount(row,row==0?(selected==1?state.max_deposit:state.max_withdraw):
        (selected==1?state.max_buy[row-1]:state.max_sell[row-1]));
}
LRESULT CALLBACK window_proc(HWND window,UINT message,WPARAM w,LPARAM l) {
    switch(message) {
    case WM_CREATE:
        panel=window;
        font=CreateFontW(-12,0,0,0,FW_NORMAL,FALSE,FALSE,FALSE,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,DEFAULT_QUALITY,DEFAULT_PITCH,L"Tahoma");
        white=CreateSolidBrush(RGB(255,255,255));
        button(title_close,L"x",490,3,22,21);
        for(int row=0;row<3;++row) {
            inputs[row]=CreateWindowExW(WS_EX_CLIENTEDGE,L"EDIT",row==0?L"0":L"1",WS_CHILD|WS_VISIBLE|WS_TABSTOP|ES_NUMBER|ES_AUTOHSCROLL,
                60,field_y[row],320,21,window,reinterpret_cast<HMENU>(edit_ids[row]),instance,nullptr);
            SendMessage(inputs[row],WM_SETFONT,reinterpret_cast<WPARAM>(font),TRUE); SendMessage(inputs[row],EM_SETLIMITTEXT,19,0);
            button(300+row,L"x",387,field_y[row],20);
            actions[row*2]=button(400+row*2,row==0?L"Deposit":L"Buy",413,action_y[row],89);
            actions[row*2+1]=button(401+row*2,row==0?L"Withdraw":L"Sell",413,action_y[row]+23,89);
            int count=row==0?5:4; int width=(484-(count-1)*5)/count;
            const wchar_t* cash[]={L"+1M",L"+10M",L"+100M",L"+1B",L"Max"};
            const wchar_t* items[]={L"+1",L"+10",L"+100",L"Max"};
            for(int i=0;i<count;++i) button(500+row*10+i,row==0?cash[i]:items[i],17+i*(width+5),preset_y[row],width);
        }
        button(refresh_id,L"Refresh",10,584,247); button(close_id,L"Close",263,584,247);
        SetTimer(window,1,250,nullptr); return 0;
    case WM_PAINT: {
        PAINTSTRUCT ps; HDC dc=BeginPaint(window,&ps);
        RECT area{}; GetClientRect(window,&area);
        HDC memory=CreateCompatibleDC(dc);
        HBITMAP bitmap=CreateCompatibleBitmap(dc,area.right,area.bottom);
        if(memory && bitmap) {
            auto old=SelectObject(memory,bitmap); paint(memory);
            BitBlt(dc,0,0,area.right,area.bottom,memory,0,0,SRCCOPY);
            SelectObject(memory,old);
        } else paint(dc);
        if(bitmap) DeleteObject(bitmap);
        if(memory) DeleteDC(memory);
        EndPaint(window,&ps); return 0;
    }
    case WM_PRINTCLIENT: paint(reinterpret_cast<HDC>(w)); return 0;
    case WM_ERASEBKGND: return 1;
    case WM_CTLCOLORSTATIC:
    case WM_CTLCOLOREDIT: SetBkColor(reinterpret_cast<HDC>(w),RGB(255,255,255)); return reinterpret_cast<LRESULT>(white);
    case WM_DRAWITEM: {
        auto draw=reinterpret_cast<DRAWITEMSTRUCT*>(l); auto box=draw->rcItem;
        bool disabled=draw->itemState&ODS_DISABLED;
        gradient(draw->hDC,box,disabled?RGB(244,244,244):RGB(207,217,255),disabled?RGB(222,222,222):RGB(153,174,242));
        FrameRect(draw->hDC,&box,reinterpret_cast<HBRUSH>(GetStockObject(GRAY_BRUSH)));
        InflateRect(&box,-1,-1); FrameRect(draw->hDC,&box,reinterpret_cast<HBRUSH>(GetStockObject(WHITE_BRUSH)));
        wchar_t label[60]; GetWindowTextW(draw->hwndItem,label,60); SelectObject(draw->hDC,font);
        SetBkMode(draw->hDC,TRANSPARENT); SetTextColor(draw->hDC,disabled?RGB(139,139,139):RGB(0,0,0));
        if(draw->itemState&ODS_SELECTED) OffsetRect(&box,1,1);
        DrawTextW(draw->hDC,label,-1,&box,DT_CENTER|DT_VCENTER|DT_SINGLELINE);
        if(draw->itemState&ODS_FOCUS) { InflateRect(&box,-2,-2); DrawFocusRect(draw->hDC,&box); }
        return TRUE;
    }
    case WM_NCHITTEST: {
        POINT point{static_cast<short>(LOWORD(l)),static_cast<short>(HIWORD(l))}; ScreenToClient(window,&point);
        if(point.y>=0 && point.y<27 && point.x<485) return HTCAPTION;
        break;
    }
    case WM_COMMAND: {
        int id=LOWORD(w);
        if(HIWORD(w)==EN_CHANGE) { update(); return 0; }
        if(id==close_id || id==title_close || id==IDCANCEL) { ShowWindow(window,SW_HIDE); return 0; }
        if(id==refresh_id) { submit(pn_bank::Refresh); return 0; }
        if(id>=300 && id<303) { set_amount(id-300,0); return 0; }
        if(id>=400 && id<406) { submit(id-399,amount((id-400)/2)); return 0; }
        if(id>=500 && id<530) {
            int row=(id-500)/10, index=(id-500)%10;
            if(index==(row==0?4:3)) max_menu(row,reinterpret_cast<HWND>(l));
            else {
                int64_t cash[]={1000000,10000000,100000000,1000000000}, item[]={1,10,100};
                int64_t value=std::min<int64_t>(pn_bank::wallet_limit,std::max<int64_t>(0,amount(row)));
                set_amount(row,std::min<int64_t>(pn_bank::wallet_limit,value+(row==0?cash[index]:item[index])));
            }
            return 0;
        }
        break;
    }
    case BANK_OPEN: show(); return 0;
    case BANK_REMOTE_OPEN:
        if(bank_current_generation(static_cast<LONG>(w))) show();
        return 0;
    case BANK_SESSION:
        if(!bank_current_generation(static_cast<LONG>(w),false)) return 0;
        busy=refreshing=verified=last_reply_connected=false;
        queued_action=pn_bank::Refresh; queued_amount=0; state=pn_bank::Reply{}; sequence=0;
        for(int row=0;row<3;++row) set_amount(row,row==0?0:1);
        status=L"Log in to a character to use the bank.";
        if(bank_authenticated()) submit(pn_bank::Refresh);
        update("session_changed"); return 0;
    case BANK_RESULT: {
        auto result=reinterpret_cast<BankResult*>(l);
        if(bank_current_generation(result->generation)) {
            const bool unchanged=refreshing && verified && result->connected &&
                queued_action==pn_bank::Refresh && !std::memcmp(&state,&result->state,sizeof(state));
            const auto next_action=queued_action; const auto next_amount=queued_amount;
            busy=refreshing=false; queued_action=pn_bank::Refresh; queued_amount=0;
            last_reply_connected=result->connected;
            if(result->connected) {
                state=result->state; sequence=std::max(sequence,state.request_id);
                verified=state.result!=pn_bank::Unauthorized;
                if(!unchanged) status=wide(pn_bank::message(state.result));
            } else {
                verified=false; status=L"Connection lost. Refresh to verify the transaction result.";
            }
            if(next_action!=pn_bank::Refresh && result->connected && state.result==pn_bank::Ok && actions_ready()) {
                const auto plan=pn_bank::plan(state,next_action,next_amount);
                if(plan.result==pn_bank::Ok) submit(next_action,next_amount);
                else { status=wide(pn_bank::message(plan.result)); update("queued_action_rejected"); }
            } else if(!unchanged) update("reply_received");
            else write_diagnostics("refresh_unchanged");
        }
        delete result; return 0;
    }
    case WM_TIMER:
        if(!preview && (!game || !IsWindow(game))) {
            game=bank_find_game_window();
            if(game) previous_game_proc=reinterpret_cast<WNDPROC>(SetWindowLongPtr(game,GWLP_WNDPROC,reinterpret_cast<LONG_PTR>(game_proc)));
        }
        // Authenticate while hidden so the game's bank button/NPC/@bank can
        // open this panel through a server notification. Hidden keepalives are
        // infrequent; failed early logins and disconnected sockets retry.
        if(!preview && bank_authenticated() && !busy && GetTickCount64()-last_refresh>
            (state.result==pn_bank::Saving?500:(!verified || IsWindowVisible(window) || !bank_connection_ready()?3000:15000))) submit(pn_bank::Refresh);
        return 0;
    case WM_CLOSE: ShowWindow(window,SW_HIDE); return 0;
    case WM_DESTROY: KillTimer(window,1); PostQuitMessage(0); return 0;
    }
    return DefWindowProcW(window,message,w,l);
}
void save_preview(const char* path="bank-preview.bmp") {
    // Render our own hidden window and its controls, without capturing the desktop.
    HDC screen=GetDC(nullptr), memory=CreateCompatibleDC(screen);
    BITMAPINFO info{}; info.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
    info.bmiHeader.biWidth=520; info.bmiHeader.biHeight=-640; info.bmiHeader.biPlanes=1; info.bmiHeader.biBitCount=32;
    void* bits=nullptr; HBITMAP bitmap=CreateDIBSection(screen,&info,DIB_RGB_COLORS,&bits,nullptr,0);
    auto old=SelectObject(memory,bitmap);
    SendMessage(panel,WM_PRINT,reinterpret_cast<WPARAM>(memory),PRF_CLIENT|PRF_CHILDREN|PRF_ERASEBKGND);
    BITMAPFILEHEADER header{}; header.bfType=0x4d42; header.bfOffBits=sizeof(header)+sizeof(info.bmiHeader);
    header.bfSize=header.bfOffBits+520*640*4;
    FILE* output=fopen(path,"wb");
    if(output) { fwrite(&header,sizeof(header),1,output); fwrite(&info.bmiHeader,sizeof(info.bmiHeader),1,output); fwrite(bits,520*640*4,1,output); fclose(output); }
    SelectObject(memory,old); DeleteObject(bitmap); DeleteDC(memory); ReleaseDC(nullptr,screen);
}
}

int bank_window_main(HINSTANCE module,bool render) {
    instance=module; preview=render;
    WNDCLASSW type{}; type.lpfnWndProc=window_proc; type.hInstance=instance;
    type.hCursor=LoadCursor(nullptr,IDC_ARROW); type.lpszClassName=L"PNAccountBank";
    RegisterClassW(&type);
    panel=CreateWindowExW(WS_EX_TOOLWINDOW|WS_EX_CONTROLPARENT,type.lpszClassName,L"Bank",WS_POPUP|WS_BORDER|WS_CLIPCHILDREN,
        100,100,522,642,nullptr,nullptr,instance,nullptr);
    if(!panel) return 1;
    bank_install_transport(panel);
    if(!preview) configure_diagnostics();
    if(preview) {
        state.result=pn_bank::Ok; state.bank=1834023229; state.wallet=0;
        state.max_deposit=0; state.max_withdraw=state.bank;
        state.counts[0]=1;state.counts[1]=10;
        for(int i=0;i<2;++i) { state.max_buy[i]=state.bank/state.buy[i]; state.max_sell[i]=state.counts[i]; }
        verified=true; status=L"Choose a banking action.";
        set_amount(0,INT64_MAX); assert(!IsWindowEnabled(actions[0]) && !IsWindowEnabled(actions[1]));
        SendMessage(panel,WM_COMMAND,500,0); assert(amount(0)==pn_bank::wallet_limit);
        set_amount(1,3); assert(IsWindowEnabled(actions[2]));
        set_amount(1,4); assert(!IsWindowEnabled(actions[2]));
        set_amount(0,0); set_amount(1,1); set_amount(2,1); update(); save_preview();
        state.bank=INT64_MAX;state.wallet=INT32_MAX;state.max_deposit=state.max_withdraw=0;
        for(int i=0;i<2;++i) { state.max_buy[i]=30000; state.max_sell[i]=0; }
        set_amount(0,1);assert(!IsWindowEnabled(actions[0]) && !IsWindowEnabled(actions[1]));
        save_preview("bank-preview-max.bmp");
        state.bank=1000000;state.wallet=1000000000;state.max_deposit=state.wallet;
        state.max_withdraw=state.bank;
        for(int i=0;i<2;++i) state.counts[i]=state.max_buy[i]=state.max_sell[i]=0;
        update(); save_preview("bank-preview-needs-deposit.bmp");
        DestroyWindow(panel); return 0;
    }
    update();
    MSG message;
    while(GetMessage(&message,nullptr,0,0)>0) {
        if(!IsWindowVisible(panel) || !IsDialogMessage(panel,&message)) { TranslateMessage(&message); DispatchMessage(&message); }
    }
    return 0;
}
#ifdef PN_BANK_PREVIEW
int main() { return bank_window_main(GetModuleHandle(nullptr),true); }
#elif !defined(PN_BANK_UI_TEST)
static DWORD WINAPI bank_start(void* module) { return bank_window_main(static_cast<HINSTANCE>(module),false); }
BOOL WINAPI DllMain(HINSTANCE module,DWORD reason,void*) {
    if(reason==DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(module);
        HANDLE thread=CreateThread(nullptr,0,bank_start,module,0,nullptr); if(thread) CloseHandle(thread);
    }
    return TRUE;
}
#endif
