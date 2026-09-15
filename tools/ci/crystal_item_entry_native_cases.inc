// Native queue/dequeue/timer plus native item use and NPC continuation. The one
// event-name lookup, packet delivery and inherited world/registry are doubles.
extern int32 npc_event_sub(map_session_data*,event_data*,const char*);
static event_data crystal_entry_event{};
static unsigned crystal_event_lookups=0,crystal_item_acks=0;
extern "C" int32 crystal_event_lookup(map_session_data*,const char*,int32) asm("__wrap__Z9npc_eventP16map_session_dataPKci");
extern "C" int32 crystal_event_lookup(map_session_data* sd,const char* event,int32 touch){
 check(sd==attached&&touch==0&&std::string(event)=="CH2_PhantomCrystal::OnOpen","single explicit crystal event registry lookup");
 check(crystal_entry_event.nd&&crystal_entry_event.nd->u.scr.script,"fixture registered full actual bridge");
 ++crystal_event_lookups;return npc_event_sub(sd,&crystal_entry_event,event);
}
extern "C" void crystal_use_ack(const map_session_data*,int32,int32,bool) asm("__wrap__Z15clif_useitemackPK16map_session_dataiib");
extern "C" void crystal_use_ack(const map_session_data* sd,int32 index,int32 amount,bool ok){
 check(sd==attached&&index==0&&amount==2&&ok,"actual delay-consume use acknowledgement retains crystal");++crystal_item_acks;
}
extern "C" void crystal_clear_unit(uint32,clr_type,const map_session_data&) asm("__wrap__Z21clif_clearunit_singlej8clr_typeRK16map_session_data");
extern "C" void crystal_clear_unit(uint32,clr_type,const map_session_data& sd){check(&sd==attached,"clear-unit transport owner");}

void crystal_entry_setup(map_session_data* sd){
 sd->state={};sd->state.ignoretimeout=true;sd->progressbar={};
 sd->status.class_=JOB_NOVICE;sd->class_=MAPID_NOVICE;sd->status.sex=SEX_MALE;
 sd->ud.skilltimer=INVALID_TIMER;sd->npc_id=0;sd->state.menu_or_input=0;sd->npc_menu=0;
 sd->canuseitem_tick=0;sd->canusecashfood_tick=0;
 // Use normal map-flag initialization; an empty flags vector is not a valid map.
 ::map[0].initMapFlags();
 check(!::map[0].getMapFlag(MF_NOITEMCONSUMPTION)&&!::map[0].getMapFlag(MF_NOBRANCH)&&!::map[0].getMapFlag(MF_GVG),"fixture map has ordinary unrestricted item-use flags");
 for(auto& timer:sd->eventtimer)timer=INVALID_TIMER;
 sd->eventcount=0;crystal_event_lookups=crystal_item_acks=0;
 put(0,106441,2);weight();
}
void crystal_entry_finish(map_session_data* sd,int choice){
 unsigned pauses=0;
 while(sd->st){
  check(++pauses<8,"bounded actual crystal NPC continuation");
  bool closing=sd->st->state==CLOSE;
  if(sd->st->state==RERUNLINE)sd->npc_menu=choice;
  else check(closing||sd->st->state==STOP,"actual choice has expected suspension");
  check(!npc_scriptcont(sd,NPC,closing),"native bridge near/ownership/continuation accepted");
 }
}
void shop_cases(const std::string& dir){
 const unsigned first=cases;
 for(const char* name:{"CH2_CanGrantMaterial","CH2_OpenPhantomCrystal"}){
  auto* code=compile(read(dir+"/"+name+".script"),name);strdb_put(script_get_userfunc_db(),name,code);
 }
 const auto bridge_text=read(dir+"/CH2_PhantomCrystal.script");
 auto* bridge=parse_script(bridge_text.c_str(),"actual crystal event bridge",1,SCRIPT_USE_LABEL_DB);
 check(bridge&&errors==0,"complete bridge source parsed natively");
 check(strdb_exists(script_get_label_db(),"OnOpen"),"actual parsed OnOpen label exists");
 crystal_entry_event.nd=&crystal_npc;crystal_entry_event.pos=strdb_iget(script_get_label_db(),"OnOpen");
 crystal_npc.u.scr.script=bridge;crystal_npc.class_=-1;
 std::strcpy(crystal_npc.exname,"CH2_PhantomCrystal");
 auto definition=item_db.find(106441);check(definition&&definition->flag.delay_consume>0,"actual item is delay-consume");
 auto* candidate_item=definition->script;
 auto* direct_item=compile(read(dir+"/direct-crystal.script"),"actual earlier direct-call item script");
 {
  auto sd=recipient();crystal_entry_setup(sd.get());definition->script=direct_item;
  check(pc_useitem(sd.get(),0)==1,"actual pc_useitem executes direct-call original");
  check(errors==0&&crystal_item_acks==1&&!messages.empty(),"original produced initial native dialog");
  check(!sd->st&&crystal_event_lookups==0&&sd->eventcount==0,"pc_useitem freed original suspended menu and queued no continuation");
  check(count(106441)==2,"original delay-consume crystal remains but cannot complete menu");
 }
 definition->script=candidate_item;script_free_code(direct_item);
 for(int mode=0;mode<5;++mode){
  auto sd=recipient();crystal_entry_setup(sd.get());
  check(pc_useitem(sd.get(),0)==1,"actual pc_useitem accepts bridged item");
  check(errors==0&&crystal_item_acks==1&&!sd->st&&count(106441)==2,"bridge item returns without abandoned dialog or consumption");
  check(crystal_event_lookups==1&&sd->eventcount==1&&sd->eventqueue[0][0]==0,"native doevent queued and native dequeue scheduled event timer");
  do_timer(gettick()+200);
  check(errors==0&&crystal_event_lookups==2&&sd->eventcount==0,"native timer dispatched registered bridge after item use returned");
  check(sd->st&&sd->st->state==STOP&&sd->npc_id==NPC,"queued bridge owns a live resumable NPC dialog");
  check(npc_checknear(sd.get(),&crystal_npc)==&crystal_npc,"classless bridge remains reachable through native NPC near check");
  if(mode==2)sd->status.inventory_slots=1;
  if(mode==3)sd->max_weight=sd->weight;
  if(mode==4){sd->st->state=END;run_script_main(sd->st);} // Explicit interruption double, not network disconnect.
  else crystal_entry_finish(sd.get(),mode==1?7:1);
  const bool success=mode<2;
  check(errors==0&&!sd->st,"bridged choice completes without native errors");
  check(count(106441)==(success?1:2),"only successful selected delivery consumes crystal");
  check(count(1001997)==(mode==0?1:0)&&count(1002002)==(mode==1?1:0),"only exact selected first or seventh material delivered");
  for(int id:{1002011,1002014,1001999,1002000,1002001})check(count(id)==0,"unselected materials remain absent");
 }
 crystal_npc.u.scr.script=nullptr;script_free_code(bridge);crystal_entry_event={};
 std::printf("CRYSTAL_ITEM_ENTRY_NATIVE_OK cases=%u original_direct_failure=1 queue_and_timer=native event_lookup=fixture\n",cases-first);
}
