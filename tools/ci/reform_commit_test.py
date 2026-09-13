#!/usr/bin/env python3
"""Exercise the production commit/retry protocol with delayed and stale replies."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
source = (ROOT / 'src/map/intif.cpp').read_text()
begin = source.index('static void intif_reform_save_request(')
end = source.index('\nint32 intif_clan_requestclans()', begin)
prefix = r'''
#include <cassert>
#include <cstdint>
#include <cstring>
#include <iostream>
using uint64=uint64_t;using uint16=uint16_t;using int32=int32_t;
struct s_storage {int marker=0;};
struct map_session_data {
 struct {uint64 item_reform_save_id=0;uint16 item_reform_save_index=0;} state;
 struct {int account_id=11,char_id=12;} status;
 s_storage inventory;
};
map_session_data player;bool present=true,connected=true;int sends=0,acks=0,timers=0;
uint64 sent[32]={},received[32]={};char bytes[128]={};
int inter_fd=1;
#define WFIFOHEAD(fd,len) ((void)0)
#define WFIFOW(fd,off) sent[off]
#define WFIFOL(fd,off) sent[off]
#define WFIFOQ(fd,off) sent[off]
#define WFIFOP(fd,off) (bytes+off)
#define WFIFOSET(fd,len) (++sends)
#define RFIFOL(fd,off) received[off]
#define RFIFOQ(fd,off) received[off]
#define RFIFOB(fd,off) received[off]
#define TIMER_FUNC(name) int name(int tid,int64_t tick,int id,intptr_t data)
int CheckForCharServer(){return !connected;}
bool chrif_isconnected(){return connected;}
map_session_data* map_id2sd(int id){return present&&id==player.status.account_id?&player:nullptr;}
int64_t gettick(){return 100;}
void add_timer(int64_t,int(*)(int,int64_t,int,intptr_t),int,intptr_t){++timers;}
void clif_item_reform_result(map_session_data&,uint16 index,int result){assert(index==3&&result==0);++acks;}
'''
suffix = r'''
int main(){
 player.inventory.marker=40;
 intif_reform_save(player,3);auto first=player.state.item_reform_save_id;
 assert(first!=0&&sends==1&&acks==0&&timers==1);
 assert(sent[0]==0x308d&&sent[2]==20+sizeof(s_storage)&&sent[4]==11&&sent[8]==12&&sent[12]==first);
 received[2]=11;received[6]=12;received[10]=first;received[18]=0;
 intif_parse_InventoryCommitted(1);assert(acks==0&&player.state.item_reform_save_id==first);
 connected=false;intif_reform_save_retry(1,1100,11,first);assert(sends==1&&timers==2);
 connected=true;player.inventory.marker=99;
 intif_reform_save_retry(1,2100,11,first);s_storage snapshot;memcpy(&snapshot,bytes+20,sizeof(snapshot));
 assert(sends==2&&snapshot.marker==99&&acks==0);
 received[18]=1;received[6]=13;intif_parse_InventoryCommitted(1);assert(acks==0);
 received[6]=12;received[10]=first+1;intif_parse_InventoryCommitted(1);assert(acks==0);
 received[10]=first;intif_parse_InventoryCommitted(1);assert(acks==1&&player.state.item_reform_save_id==0);
 intif_parse_InventoryCommitted(1);assert(acks==1);
 int oldtimers=timers;intif_reform_save_retry(1,3100,11,first);assert(timers==oldtimers&&sends==2);
 intif_reform_save(player,3);auto second=player.state.item_reform_save_id;assert(second!=first);
 intif_parse_InventoryCommitted(1);assert(acks==1&&player.state.item_reform_save_id==second);
 oldtimers=timers;intif_reform_save_retry(1,4100,11,first);assert(timers==oldtimers);
 present=false;intif_reform_save_retry(1,4100,11,second);assert(timers==oldtimers);
 present=true;received[10]=second;intif_parse_InventoryCommitted(1);assert(acks==2);
 std::cout<<"PASS: production reform commit protocol: delayed/failure/stale/duplicate replies, reconnect, current-snapshot retry, logout\n";
}
'''
with tempfile.TemporaryDirectory(prefix='pn-reform-commit-') as temp:
    cpp = Path(temp) / 'test.cpp'
    binary = Path(temp) / 'test'
    cpp.write_text(prefix + source[begin:end] + suffix)
    subprocess.run(['g++', '-std=c++17', '-O1', '-fsanitize=address,undefined', '-o', str(binary), str(cpp)], check=True)
    subprocess.run([str(binary)], check=True)
