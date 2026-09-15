// Actual complete merchant bodies, parser, menu/input suspension and native grants.
// Explicit fixture/world/transport/persistence boundaries are inherited from the host.
extern "C" void merchant_input(map_session_data&,uint32) asm("__wrap__Z16clif_scriptinputR16map_session_dataj");
extern "C" void merchant_input(map_session_data& sd,uint32){check(&sd==attached,"numeric input transport owner");}
struct MerchantRecipe {
 const char* script; std::vector<int> answers; int output,amount,currency,cost,cancel; bool stackable,bowl;
};
void merchant_walk(script_code* code,const std::vector<int>& answers,const std::function<void()>& last={},bool disconnect=false){
 auto* sd=attached;sd->state.menu_or_input=0;sd->npc_menu=0;sd->npc_amount=0;
 run_script(code,0,sd->id,NPC);unsigned pauses=0,answer=0;
 while(sd->st){
  check(++pauses<45,"merchant bounded real dialogue");auto* st=sd->st;
  if(st->state==RERUNLINE){
   check(answer<answers.size(),"merchant exact answer count");
   if(answer+1==answers.size()){
    if(last)last();
    if(disconnect){st->state=END;run_script_main(st);break;}
   }
   sd->npc_menu=answers[answer];sd->npc_amount=answers[answer++];
  }else if(st->state==CLOSE)st->state=END;
  else check(st->state==STOP,"merchant known suspension");
  run_script_main(st);
 }
 check(disconnect?answer+1==answers.size():answer==answers.size(),"merchant traversed requested full path");
}
void shop_cases(const std::string& dir){
 const unsigned first=cases;const bool negative=std::getenv("MERCHANT_NEGATIVE")!=nullptr;
 std::vector<MerchantRecipe> recipes={
  {"erundek",{1,1,1,1,2,1},13036,1,7828,100,2,false,false},
  {"erundek",{1,2,1,1,2,1},2538,1,7828,50,3,false,false}
 };
 const int ration_cost[]={10,10,5,10,10};
 for(int i=0;i<5;++i)recipes.push_back({"erundek",{1,4,i+1,2,1},12269+i,1,7828,ration_cost[i],3,true,false});
 const int manuals[]={7144,7127,7128,7129,7130,7131,7132,7133};
 for(int i=0;i<8;++i)recipes.push_back({"alchemist",{2,i+1,1},manuals[i],1,0,i==7?240000:100000,2,true,false});
 for(int qty:{1,2000})recipes.push_back({"alchemist",{1,1,qty},7134,qty,0,qty*8,0,true,true});
 for(const auto& r:recipes){auto d=item_db.find(r.output);check(d&&itemdb_isstackable2(d.get())==r.stackable&&!d->flag.guid&&!d->flag.autoequip&&!d->stack.inventory,"actual merchant plain/equipment metadata contract");}
 unsigned expected_failures=0,expected_zeny_errors=0;
 for(size_t recipe=0;recipe<recipes.size();++recipe){
  const auto& r=recipes[recipe];
  std::vector<int> modes;
  if(negative){if(recipe==0||recipe==1||recipe==15)modes={1};else if(recipe==7)modes={3};}
  else {modes={0,1,3,4,5,14};if(item_db.find(r.output)->weight)modes.push_back(2);if(r.stackable)for(int i=6;i<=13;++i)modes.push_back(i);}
  for(int mode:modes){
   auto sd=recipient();sd->status.zeny=r.currency?1234567:r.cost*2;
   if(r.currency)put(0,r.currency,r.cost*2);else put(0,644,1);weight();
   auto* code=compile(read(dir+"/merchant-"+r.script+(negative?"-before.script":"-after.script")),"actual full merchant");
   auto answers=r.answers;if(mode==4)answers.back()=r.cancel;
   std::unique_ptr<Snapshot> before;int old_output=0,old_currency=0,old_zeny=0;
   merchant_walk(code,answers,[&](){
    if(mode==1)sd->status.inventory_slots=1;
    if(mode==2)sd->max_weight=sd->weight;
    if(mode==3){if(r.currency)put(0,r.currency,r.cost-1);else sd->status.zeny=r.cost-1;}
    if(mode==14)for(int i=1;i<MAX_INVENTORY;++i)put(i,644,1);
    if(mode>=6&&mode<=13){
     int first_amount=(mode==7||mode==9)?30000:mode==10?30000-r.amount:10;
     put(1,r.output,first_amount);sd->status.inventory_slots=2;
     if(mode==6||mode==8)sd->inventory.u.items_inventory[1].bound=BOUND_ACCOUNT;
     if(mode==11)sd->inventory.u.items_inventory[1].card[0]=4700;
     if(mode==12)sd->inventory.u.items_inventory[1].unique_id=UINT64_MAX;
     if(mode==13)sd->inventory.u.items_inventory[1].expire_time=2100000000;
     if(mode==8||mode==9){put(2,r.output,10);sd->status.inventory_slots=3;}
    }
    weight();old_output=count(r.output);old_currency=r.currency?count(r.currency):0;old_zeny=sd->status.zeny;before=std::make_unique<Snapshot>();
   },mode==5);
   check(bool(before),"merchant mutation happened at real final response");
   if(!negative&&r.currency){
    bool bound_notice=false;for(const auto& message:messages)if(message.find("Character Bound")!=std::string::npos)bound_notice=true;
    check(bound_notice==!r.stackable,"Erundek bound-equipment notice excludes consumable rations");
   }
   if(negative){
    if(mode==1){
     check(errors==1&&count(r.output)==old_output,"old merchant native grant failure reproduced");++expected_failures;
     check(r.currency?count(r.currency)==old_currency-r.cost:sd->status.zeny==old_zeny-r.cost,"old merchant loses exact payment");
    }else {
     check(errors==1,"old manual emits one native parameter error after wallet changed");
     before->unchanged();++expected_zeny_errors;
    }
   }else{
    const bool success=mode==0||mode==8||mode==10;
    check(errors==0,"merchant no native grant errors");
    if(success){
     check(count(r.output)==old_output+r.amount,"merchant delivers exact selected quantity");
     check(r.currency?count(r.currency)==old_currency-r.cost:sd->status.zeny==old_zeny-r.cost,"merchant exact single payment");
     check(r.currency?sd->status.zeny==old_zeny:count(644)==1,"merchant unrelated assets unchanged");
     if(mode==8)check(sd->inventory.u.items_inventory[1].amount==10&&sd->inventory.u.items_inventory[1].bound==BOUND_ACCOUNT,"bound first stack untouched when plain later fits");
    }else before->unchanged();
    if(mode==1){
     sd->status.inventory_slots=MAX_INVENTORY;merchant_walk(code,r.answers);
     check(errors==0&&count(r.output)==r.amount,"merchant capacity refusal remains retryable");
     check(r.currency?count(r.currency)==old_currency-r.cost:sd->status.zeny==old_zeny-r.cost,"merchant retry charges once");
    }
   }
   script_free_code(code);
  }
 }
 check(!negative||expected_failures==3,"merchant exact three historical grant failures");
 check(!negative||expected_zeny_errors==1,"merchant exact one historical wallet parameter error");
 // Each historical case above pins its own error count. Clear only the final
 // acknowledged bowl error so the host still checks for new cleanup errors.
 if(negative){check(errors==1,"last historical bowl has exactly its expected grant error");errors=0;}
 std::printf("MERCHANT_NATIVE_OK cases=%u negative=%d expected_grant_failures=%u expected_zeny_errors=%u\n",cases-first,negative,expected_failures,expected_zeny_errors);
}
