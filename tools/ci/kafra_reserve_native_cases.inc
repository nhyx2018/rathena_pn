// Complete source body under the actual parser/VM. Transport/registry/world
// doubles are inherited. Lottery cases end before animation and prize delivery;
// the candidate must not charge for an undelivered prize.
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
void kafra_full_lottery(script_code* code,bool second,int mode){
 auto sd=recipient();put(0,644,1);weight();
 sd->x=sd->y=100;crystal_npc.x=crystal_npc.y=100;
 const int price=second?5000:1000;
 setnum("RESRVPTS",price+100);
 sd->state.menu_or_input=0;sd->npc_menu=0;sd->npc_amount=0;
 const std::vector<int> answers=second?std::vector<int>{1,1}:std::vector<int>{10,1,1};
 const unsigned confirmed=2;
 const std::vector<int> ids=second?std::vector<int>{501,645,505,608}:std::vector<int>{516,602,2403,2328};
 int old_total=0;for(int id:ids)old_total+=count(id);
 bool boundary=false;unsigned answer=0,pauses=0;
 run_script(code,0,sd->id,NPC);
 while(sd->st){
  check(++pauses<40,"Kafra full lottery dialogue remains bounded");auto* st=sd->st;
  if(st->state==RERUNLINE){
   check(answer<answers.size(),"Kafra full lottery expected menu or numeric input");
   sd->npc_menu=answers[answer];sd->npc_amount=answers[answer++];
  }else if(st->state==CLOSE)st->state=END;
  else{
   check(st->state==STOP,"Kafra full lottery known Next suspension");
   if(!boundary&&answer==confirmed){
    boundary=true;
    check(nums[add_str("RESRVPTS")]==price+100,"Kafra no payment before prize delivery");
    if(mode==1)sd->status.inventory_slots=1;
    if(mode==2)st->state=END;
   }
  }
  run_script_main(st);
 }
 check(boundary,"Kafra full lottery passed final confirmation");
 int total=0;for(int id:ids)total+=count(id);
 check(errors==0,"Kafra full lottery has no native grant errors");
 check(nums[add_str("RESRVPTS")]==price+100-(mode==0?price:0),"Kafra full lottery charges only delivered prize");
 check(mode==0?total>old_total:total==old_total,"Kafra full lottery exact delivery or no output");
}
void shop_cases(const std::string& dir){
 const unsigned start=cases;const bool negative=std::getenv("KAFRA_NEGATIVE")!=nullptr;
 auto* suffix=compile(read(dir+"/kafra-num-suffix.script"),"actual F_GetNumSuffix dependency");
 strdb_put(script_get_userfunc_db(),"F_GetNumSuffix",suffix);
 auto* lottery_helper=compile(read(dir+"/kafra-lottery-helper.script"),"actual Kafra lottery delivery helper");
 strdb_put(script_get_userfunc_db(),"F_ReserveLotteryGrant",lottery_helper);
 auto* reserve2=compile(read(dir+"/kafra-reserve2.script"),"actual full Kafra reserve2");
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
   check(nums[add_str("RESRVPTS")]==(negative?5000-price:balance),"Kafra lottery keeps points until prize delivery");
   script_free_code(code);
  }
 }
 if(!negative){
  for(int mode:{0,1,2}){
   auto* first=compile(read(dir+"/kafra-after.script"),"complete Kafra reserve1 lottery");
   kafra_full_lottery(first,false,mode);script_free_code(first);
   kafra_full_lottery(reserve2,true,mode);
  }
  // Execute the actual shared function through the native VM for every
   // lottery output, including the three two-item prize batches.
  const std::vector<std::tuple<int,int,int,int,int>> prizes={
   {1000,516,100,0,0},{1000,602,4,0,0},{1000,2403,1,0,0},{1000,2328,1,0,0},
   {3000,501,100,0,0},{3000,2201,1,0,0},{3000,2226,1,0,0},{3000,505,3,0,0},
   {5000,501,150,0,0},{5000,645,15,0,0},{5000,505,3,0,0},{5000,608,1,0,0},
   {7000,504,10,0,0},{7000,656,15,0,0},{7000,657,10,0,0},{7000,608,1,607,1},
   {10000,504,30,0,0},{10000,505,10,0,0},{10000,608,1,526,10},{10000,607,3,608,2}
  };
  for(auto [price,id1,amount1,id2,amount2]:prizes){
   for(int mode:{0,1,2}){
    auto sd=recipient();put(0,644,1);weight();setnum("RESRVPTS",mode==1?price-1:price+100);
    if(mode==2)sd->status.inventory_slots=1;
    const int old1=count(id1),old2=id2?count(id2):0;
    std::ostringstream source;
    source<<"{ ARG0=callfunc(\"F_ReserveLotteryGrant\","<<price<<","<<id1<<","<<amount1<<","<<id2<<","<<amount2<<"); end; }";
    auto* code=compile(source.str(),"actual Kafra lottery native delivery");
    run_script(code,0,sd->id,NPC);
    check(!sd->st&&errors==0,"Kafra lottery native delivery completes without grant error");
    const bool success=mode==0;
    check(nums[add_str("ARG0")]==success,"Kafra lottery reports delivery only on success");
    check(nums[add_str("RESRVPTS")] == (mode==1?price-1:price+100-(success?price:0)),"Kafra lottery never charges a failed delivery");
    check(count(id1)==old1+(success?amount1:0),"Kafra first prize quantity exact");
    if(id2)check(count(id2)==old2+(success?amount2:0),"Kafra second prize quantity exact");
    script_free_code(code);
   }
  }
 }
 check(!negative||grant_failures==4,"Kafra exactly four historical native failed grants");
 script_free_code(reserve2);
 std::printf("KAFRA_RESERVE_NATIVE_OK cases=%u negative=%d expected_grant_failures=%u\n",cases-start,negative,grant_failures);
}
