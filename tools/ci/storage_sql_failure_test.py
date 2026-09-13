#!/usr/bin/env python3
"""Exercise the real item SQL save/load functions with failed result fetching.

The SQL boundary is a deterministic double; production loops and item layout are
extracted unchanged. This does not contact any database or player account.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, default=ROOT / 'src/char/char.cpp')
args = parser.parse_args()
source = args.source.read_text()
begin = source.index('int32 char_memitemdata_to_sql(')
end = source.index('\n/**', source.index('bool char_memitemdata_from_sql(', begin))
mmo = (ROOT / 'src/common/mmo.hpp').read_text()
item_begin = mmo.index('struct s_item_randomoption {')
item_end = mmo.index('// NetBSD', item_begin)

prefix = r'''
#include <algorithm>
#include <cstdarg>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <cstdio>
#include <inttypes.h>
#include <iostream>
#include <memory>
#include <string>
#include <vector>
#include "custom/multi_storage.hpp"
using int8=int8_t; using uint8=uint8_t; using int16=int16_t;
using int32=int32_t; using uint32=uint32_t; using uint64=uint64_t;
using t_itemid=uint32;
constexpr int MAX_SLOTS=4, MAX_ITEM_RDM_OPT=5;
constexpr int MAX_INVENTORY=4,MAX_CART=4,MAX_STORAGE=4,MAX_GUILD_STORAGE=4;
constexpr int SQL_SUCCESS=0,SQL_ERROR=-1,SQL_NO_DATA=100;
enum storage_type {TABLE_INVENTORY,TABLE_CART,TABLE_STORAGE,TABLE_GUILD_STORAGE};
enum SqlDataType {SQLDT_CHAR,SQLDT_INT8,SQLDT_INT16,SQLDT_INT32,SQLDT_UINT32,SQLDT_UINT64,SQLDT_ULONGLONG};
'''
boundary = r'''
struct s_storage {
 int id=0; storage_type type=TABLE_INVENTORY; uint8 stor_id=0; int amount=0,max_amount=0;
 union {item items_inventory[4];item items_cart[4];item items_storage[4];item items_guild[4];} u{};
};
struct s_storage_table {const char* name="Storage";const char* table="storage";int max_num=4;};
struct {std::shared_ptr<s_storage_table> find(uint8){return std::make_shared<s_storage_table>();}} interServerDb;
struct {const char* inventory_db="inventory";const char* cart_db="cart_inventory";
 const char* guild_storage_db="guild_storage";} schema_config;
int inter_guild_storagemax(int){return 4;}
int handle=0;int* sql_handle=&handle;
struct StringBuf {std::string text;};
void StringBuf_Init(StringBuf* b){b->text.clear();}
void StringBuf_Clear(StringBuf* b){b->text.clear();}
void StringBuf_AppendStr(StringBuf* b,const char* s){b->text+=s;}
void StringBuf_Printf(StringBuf* b,const char* fmt,...){char temp[16384];va_list args;va_start(args,fmt);vsnprintf(temp,sizeof(temp),fmt,args);va_end(args);b->text+=temp;}
const char* StringBuf_Value(StringBuf* b){return b->text.c_str();}
#define ARR_FIND(start,end,i,condition) for((i)=(start);(i)<(end);++(i)) if(condition) break
#define aCalloc(n,size) calloc(n,size)
#define aFree(p) free(p)
void ShowInfo(const char*,...){}
void ShowError(const char*,...){}
void Sql_ShowDebug(int*){}
std::vector<item> rows;
std::vector<std::string> writes;
int fail_at=-1;bool invalid_bound_binding=false;
int Sql_QueryStr(int*,const char* query){writes.emplace_back(query);return SQL_SUCCESS;}
int Sql_Query(int*,const char* query,...){writes.emplace_back(query);return SQL_SUCCESS;}
struct SqlStmt {
 void* columns[32]{};size_t widths[32]{};size_t row=0;
 explicit SqlStmt(int&){}
 int PrepareStr(const char*){return SQL_SUCCESS;}
 int BindParam(int,SqlDataType,void*,int){return SQL_SUCCESS;}
 int Execute(){return SQL_SUCCESS;}
 int BindColumn(size_t i,SqlDataType type,void* target){
  columns[i]=target; widths[i]=type==SQLDT_CHAR||type==SQLDT_INT8?1:type==SQLDT_INT16?2:type==SQLDT_INT32||type==SQLDT_UINT32?4:8;
  if(i==8 && widths[i]!=sizeof(item::bound)) invalid_bound_binding=true;
  return SQL_SUCCESS;
 }
 int NextRow(){
  if(static_cast<int>(row)==fail_at) return SQL_ERROR;
  if(row>=rows.size()) return SQL_NO_DATA;
  // Column zero always points at item.id, the first member of the actual packed layout.
  std::memcpy(columns[0],&rows[row++],sizeof(item));
  return SQL_SUCCESS;
 }
};
void SqlStmt_ShowDebug(SqlStmt&){}
'''
suffix = r'''
int failures=0,cases=0;
void check(bool condition,const char* name,storage_type type){++cases;if(!condition){++failures;std::cerr<<"FAIL "<<name<<" storage="<<type<<"\n";}}
item make_item(int id){item v{};v.id=id;v.nameid=500+id;v.amount=1;v.unique_id=0x123456789abcdefULL;v.bound=2;return v;}
void reset(){rows.clear();writes.clear();fail_at=-1;invalid_bound_binding=false;}
int main(){
 for(auto type:{TABLE_INVENTORY,TABLE_CART,TABLE_STORAGE,TABLE_GUILD_STORAGE}){
  item inventory[4]{};inventory[0]=make_item(1);inventory[1]=make_item(2);
  for(int failed_row:{0,1}){
   reset();rows={inventory[0],inventory[1]};fail_at=failed_row;
   int result=char_memitemdata_to_sql(inventory,4,12,type,0);
   check(result!=0,"save must report failed SQL fetch",type);
   check(writes.empty(),"unchanged items must not be inserted after failed SQL fetch",type);
   reset();rows={inventory[0],inventory[1]};fail_at=failed_row;s_storage loaded{};
   bool success=char_memitemdata_from_sql(&loaded,4,12,type,0);
   check(!success,"load must reject failed SQL fetch",type);
   check(loaded.amount==0 && loaded.u.items_inventory[0].nameid==0,"failed load must not expose a partial inventory",type);
  }
  reset();rows={inventory[0],inventory[1]};
  fail_at=1;inventory[0].amount=2;
  check(char_memitemdata_to_sql(inventory,4,12,type,0)!=0 && writes.empty(),"late read failure must precede all SQL mutations",type);
  inventory[0].amount=1;
  reset();rows={inventory[0],inventory[1]};
  check(char_memitemdata_to_sql(inventory,4,12,type,0)==0 && writes.empty(),"valid unchanged save",type);
  check(!invalid_bound_binding,"bound column must fit its one-byte buffer",type);
  s_storage loaded{};
  check(char_memitemdata_from_sql(&loaded,4,12,type,0) && loaded.amount==2 && std::memcmp(loaded.u.items_inventory,inventory,2*sizeof(item))==0,"valid complete load preserves metadata",type);
  reset();loaded={};
  check(char_memitemdata_from_sql(&loaded,4,12,type,0) && loaded.amount==0,"empty SQL result is a valid inventory",type);
  reset();rows={inventory[0],inventory[1],make_item(3),make_item(4)};loaded={};
  check(char_memitemdata_from_sql(&loaded,4,12,type,0) && loaded.amount==4,"exactly full inventory loads",type);
  rows.push_back(make_item(5));loaded={};
  check(!char_memitemdata_from_sql(&loaded,4,12,type,0) && loaded.amount==0,"over-capacity SQL result must not be silently truncated",type);
 }
 std::cout<<cases<<" checks; "<<failures<<" failures\n";
 return failures?1:0;
}
'''
with tempfile.TemporaryDirectory(prefix='pn-storage-fetch-') as tmp:
    cpp = Path(tmp) / 'test.cpp'
    binary = Path(tmp) / 'test'
    cpp.write_text(prefix + mmo[item_begin:item_end] + boundary + source[begin:end] + suffix)
    subprocess.run(['g++', '-std=c++17', '-O1', '-g', '-fsanitize=address,undefined',
                    '-I', str(ROOT / 'src'),
                    '-o', str(binary), str(cpp)], check=True)
    raise SystemExit(subprocess.run([str(binary)]).returncode)
