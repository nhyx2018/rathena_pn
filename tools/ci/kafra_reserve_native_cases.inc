// Complete source body under the actual parser/VM. Transport/registry/world
// doubles are inherited. Lottery cases end before animation and prize delivery.
void kafra_walk(script_code* code,const std::vector<int>& answers,const std::function<void()>& final_response={},bool lottery=false){
 auto* sd=attached;sd->state.menu_or_input=0;sd->npc_menu=0;
 run_script(code,0,sd->id,NPC);unsigned pauses=0,answer=0;
 while(sd->st){
  check(++pauses<30,"Kafra bounded actual dialogue");auto* st=sd->st;
  if(st->state==RERUNLINE){
   check(answer<answers.size(),"Kafra exact answer count");
   if(answer+1==answers.size()&&final_response)final_response();
   sd->npc_menu=answers[answer++];
  }else if(st->state==CLOSE)st->state=END;
  else {
   check(st->state==STOP,"Kafra known suspension");
   if(lottery&&answer==answers.size())st->state=END;
  }
  run_script_main(st);
 }
 check(answer==answers.size(),"Kafra traversed requested real menus");
}
void shop_cases(const std::string& dir){
 const unsigned start=cases;const bool negative=std::getenv("KAFRA_NEGATIVE")!=nullptr;
 unsigned grant_failures=0;
 for(bool second:{false,true}){
  const int output=second?501:516,price=second?1100:100,amount=7;
  auto data=item_db.find(output);
  check(data&&itemdb_isstackable2(data.get())&&!data->flag.guid&&!data->flag.autoequip&&!data->stack.inventory&&data->weight>0,"Kafra native plain output contract");
  const std::vector<int> modes=negative?std::vector<int>{1,3,5,6}:std::vector<int>{0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15};
  for(int mode:modes){
   auto sd=recipient();setnum("RESRVPTS",5000);put(0,644,1);weight();
   auto* code=compile(read(dir+(negative?"/kafra-before.script":"/kafra-after.script")),"actual full Kafra reserve1");
   std::vector<int> answers=second?std::vector<int>{11,1,1}:std::vector<int>{1,1};
   if(mode==7)answers.back()=2;
   int64 point_balance=0;int old_output=0;std::unique_ptr<Snapshot> before;
   kafra_walk(code,answers,[&](){
    if(mode==1)setnum("RESRVPTS",7000);
    if(mode==2)setnum("RESRVPTS",3500);
    if(mode==3)setnum("RESRVPTS",price-1);
    if(mode==4)for(int i=1;i<MAX_INVENTORY;++i)put(i,644,1);
    if(mode==5)sd->status.inventory_slots=1;
    if(mode==6)sd->max_weight=sd->weight;
    if(mode>=8){
     put(1,output,(mode==8||mode==13)?30000:mode==14?30000-amount:10);
     if(mode==9||mode==15)sd->inventory.u.items_inventory[1].bound=BOUND_ACCOUNT;
     if(mode==10)sd->inventory.u.items_inventory[1].expire_time=2100000000;
     if(mode==11)sd->inventory.u.items_inventory[1].unique_id=UINT64_MAX;
     if(mode==12)sd->inventory.u.items_inventory[1].card[0]=4700;
     if(mode==9||mode==10||mode==11||mode==12||mode==14)sd->status.inventory_slots=2;
     if(mode==13||mode==15){put(2,output,10);sd->status.inventory_slots=3;}
    }
    weight();point_balance=nums[add_str("RESRVPTS")];old_output=count(output);before=std::make_unique<Snapshot>();
   });
   check(bool(before),"Kafra mutation reached actual final response");
   if(negative){
    check(nums[add_str("RESRVPTS")]==5000-price,"old Kafra writes stale preview balance");
    if(mode==5||mode==6){check(errors==1&&count(output)==old_output,"old Kafra lost payment on native grant failure");++grant_failures;}
    else check(errors==0&&count(output)==old_output+amount,"old Kafra grants despite changed point balance");
   }else{
    const bool success=mode==0||mode==1||mode==2||mode==14||mode==15;
    check(errors==0,"Kafra candidate no failed native grant");
    check(nums[add_str("RESRVPTS")]==point_balance-(success?price:0),"Kafra preserves changed balance and charges exact current price");
    check(count(output)==old_output+(success?amount:0),"Kafra exact ordinary reward or no reward");
    if(!success)before->unchanged();
    if(mode==15)check(sd->inventory.u.items_inventory[1].amount==10&&sd->inventory.u.items_inventory[1].bound==BOUND_ACCOUNT,"Kafra skips bound first stack and preserves it");
    if(mode==5){
     sd->status.inventory_slots=MAX_INVENTORY;kafra_walk(code,second?std::vector<int>{11,1,1}:std::vector<int>{1,1});
     check(errors==0&&count(output)==amount&&nums[add_str("RESRVPTS")]==point_balance-price,"Kafra full-slot rejection remains retryable and charges once");
    }
   }
   script_free_code(code);
  }
 }
 for(bool second:{false,true}){
  const int price=second?3000:1000;
  const std::vector<int> modes=negative?std::vector<int>{1,3}:std::vector<int>{0,1,2,3,4};
  for(int mode:modes){
   auto sd=recipient();put(0,644,1);weight();setnum("RESRVPTS",5000);
   auto* code=compile(read(dir+(negative?"/kafra-before.script":"/kafra-after.script")),"Kafra lottery common payment only");
   auto answers=second?std::vector<int>{11,10,1}:std::vector<int>{10,1};if(mode==4)answers.back()=2;
   int64 balance=0;Snapshot before;
   kafra_walk(code,answers,[&](){setnum("RESRVPTS",mode==1?7000:mode==2?3500:mode==3?price-1:5000);balance=nums[add_str("RESRVPTS")];},true);
   check(errors==0,"Kafra lottery common balance guard no VM errors");before.unchanged();
   check(nums[add_str("RESRVPTS")]==(negative?5000-price:balance-((mode==3||mode==4)?0:price)),"Kafra lottery entry charges current affordable balance exactly once");
   script_free_code(code);
  }
 }
 check(!negative||grant_failures==4,"Kafra exactly four historical native failed grants");
 std::printf("KAFRA_RESERVE_NATIVE_OK cases=%u negative=%d expected_grant_failures=%u\n",cases-start,negative,grant_failures);
}
