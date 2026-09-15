void ivar(const char* k,int64 v){i64db_i64put(instances.at(1)->regs.vars,add_str(k),v);}
void resume_dialog(map_session_data* sd,int answer=1){
 unsigned n=0;
 while(sd->st){check(++n<10,"bounded dialogue");auto* st=sd->st;
  if(st->state==RERUNLINE)sd->npc_menu=answer;
  else if(st->state==CLOSE)st->state=END;
  else check(st->state==STOP,"known suspension");
  run_script_main(st);
 }
}
void shop_cases(const std::string& dir){
 const auto start=cases;
 for(const char* name:{"F_PNLake_CanGrant","CH2_CanGrantMaterial"}){
  auto* helper=compile(read(dir+"/"+name+".script"),name);strdb_put(script_get_userfunc_db(),name,helper);
 }
 for(int id:{1001414,1001415,1001440,1001441,1001442,1001443,1001997,1002011,1002014,1001999,1002000,1002001,1002002})for(int mode=0;mode<4;++mode){
  auto sd=recipient();const char* name=id<1001900?"F_PNLake_CanGrant":"CH2_CanGrantMaterial";
  if(mode==0){variant(0,id,1,1);sd->status.inventory_slots=1;}
  if(mode==1){variant(0,id,29999,0);sd->status.inventory_slots=1;}
  if(mode==2){variant(0,id,30000,0);sd->status.inventory_slots=1;}
  if(mode==3){variant(0,id,1,1);variant(1,id,1,0);sd->status.inventory_slots=2;}
  const int before=count(id);
  std::string text="{ setarray .@ids[0],"+std::to_string(id)+"; setarray .@qty[0],1; @Capacity=callfunc(\""+name+"\",.@ids,.@qty,1); if (@Capacity) getitem "+std::to_string(id)+",1; end; }";
  auto* code=compile(text,"plain material stack boundary");run_script(code,0,sd->id,NPC);
  check(!sd->st&&errors==0,"capacity helper and actual grant complete");
  const bool ok=mode==1||mode==3;check(nums[add_str("@Capacity")]==ok,"exact bound/plain/stack-limit prediction");check(count(id)==before+(ok?1:0),"exact approved material delivery");script_free_code(code);
 }

 for(bool old:{std::getenv("REWARD_NEGATIVE")!=nullptr})for(int mode:{0,1,2,3,4}){
  auto sd=recipient();sd->state.menu_or_input=0;sd->npc_menu=0;
  put(0,25739,10);put(1,6607,20);weight();
  auto* code=compile(read(dir+(old?"/fall-before.script":"/fall-after.script")),"Fall exchange");
  run_script(code,0,sd->id,NPC);check(sd->st&&sd->st->state==STOP,"exchange Next");
  if(mode==1)sd->status.inventory_slots=2;
  if(mode==2)sd->max_weight=0;
  if(mode==3){put(0,25739,1);weight();}
  resume_dialog(sd.get(),mode==4?2:1);
  const bool success=mode==0;
  if(old&&(mode==1||mode==2))check(count(25739)==5&&count(6607)==10&&count(15388)==0&&errors>0,"original loses materials on failed grant");
  else {check(errors==0,"exchange no grant failure");check(count(15388)==(success?1:0),"exchange exact output");check(count(25739)==(success?5:mode==3?1:10)&&count(6607)==(success?10:20),"exchange preserves or charges exact cost");}
  script_free_code(code);
 }
 for(bool old:{std::getenv("REWARD_NEGATIVE")!=nullptr})for(int mode=0;mode<9;++mode){
  auto sd=recipient();sd->state.menu_or_input=0;sd->npc_menu=0;
  ivar("'stage",3);ivar("'run_token",777);ivar("'energy_item",1001440);
  setnum("PNLake_ActiveInstance",1);setnum("PNLake_ActiveToken",777);
  auto* code=compile(read(dir+(old?"/lake-before.script":"/lake-after.script")),"Lake claim");
  run_script(code,0,sd->id,NPC);check(sd->st&&sd->st->state==STOP,"Lake real confirmation pause");
  if(mode==1)sd->max_weight=0;
  if(mode==2)sd->status.inventory_slots=0;
  if(mode==3)ivar("'stage",2);
  if(mode==4)setnum("PNLake_ActiveToken",778);
  if(mode==5)setnum("PNLake_ClaimToken",777);
  if(mode==6)setnum("#PNLake_FullRewardToken",777);
  if(mode==8){sd->st->state=END;run_script_main(sd->st);}else resume_dialog(sd.get(),mode==7?2:1);
  if(old&&mode>0&&mode<7){
   check(nums[add_str("PNLake_ClaimToken")]==777,"original consumes claim after changed eligibility/capacity");
   if(mode<=2)check(errors>0&&count(1001415)==0,"original failed reward still claimed");
   else check(count(1001415)==1,"original stale eligibility still awards");
  }else{
   check(errors==0,"Lake no failed grant");check(count(1001415)==(mode==0?1:0),"Lake exact full reward or none");
   check(count(1001414)==(mode==0?30:0)&&count(1001440)==(mode==0?15:0),"Lake complete batch");
   check(nums[add_str("PNLake_ClaimToken")]==((mode==0||mode==5)?777:0),"Lake claim remains retryable");
  }
  if(!old&&(mode==1||mode==2)){
   sd->max_weight=2000000000;sd->status.inventory_slots=MAX_INVENTORY;sd->npc_menu=0;
   run_script(code,0,sd->id,NPC);resume_dialog(sd.get());
   check(count(1001415)==1&&count(1001414)==30&&count(1001440)==15,"Lake retry awards complete batch");
  }
  script_free_code(code);
 }
 for(int choice=1;choice<=7;++choice)for(int mode=0;mode<5;++mode){
  const int ids[]={1001997,1002011,1002014,1001999,1002000,1002001,1002002};
  auto sd=recipient();sd->state.menu_or_input=0;sd->npc_menu=0;put(0,106441,2);weight();
  auto* code=compile(read(dir+"/crystal-after.script"),"Phantom crystal");
  run_script(code,0,sd->id,NPC);check(sd->st&&sd->st->state==STOP,"crystal pauses before spending");
  check(count(106441)==2,"crystal retained before selection");
  if(mode==1)sd->status.inventory_slots=1;
  if(mode==2)sd->max_weight=0;
  if(mode==3){attached->inventory.u.items_inventory[0]={};attached->inventory_data[0]=nullptr;weight();}
  if(mode==4){sd->st->state=END;run_script_main(sd->st);}else resume_dialog(sd.get(),choice);
  check(errors==0,"crystal no failed grant");check(count(ids[choice-1])==(mode==0?1:0),"crystal exact selected material");
  check(count(106441)==(mode==0?1:mode==3?0:2),"crystal only consumed for delivered material");
  script_free_code(code);
 }
 std::printf("REWARD_RESUME_NATIVE_OK cases=%u negative=%d\n",cases-start,std::getenv("REWARD_NEGATIVE")!=nullptr);
}
