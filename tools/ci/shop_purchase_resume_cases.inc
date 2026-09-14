// Actual script suspension, current post-confirmation source, native inventory.
#define SHOP_ITEM_COUNT 2
void shop_cases(const std::string& dir) {
    for (bool fashion : {true,false}) for (int mode : {0,1,2,3}) {
        auto sd=recipient();
        sd->state.menu_or_input=0; sd->npc_menu=0;
        const char* currency=fashion?"#FP_Fashion":"kvm_point";
        const int itemid=fashion?41090:1201, cost=fashion?50:100;
        nums[add_str(currency)]=200;
        auto* code=compile(read(dir+(fashion?"/fashion-commit.script":"/kvm-commit.script")),"shop-confirmation-resume");
        run_script(code,0,sd->id,NPC);
        check(sd->st&&sd->st->state==STOP,"real confirmation Next suspended");
        // State changes while the confirmation window is open.
        if(mode==1) nums[add_str(currency)]=0;
        if(mode==2) { variant(0,1201,1,0); sd->max_weight=0; }
        if(mode==3) sd->status.inventory_slots=0;
        const int prior_count=count(itemid);
        unsigned pauses=0;
        while(sd->st) {
            check(++pauses<8,"bounded shop dialogue");
            auto* state=sd->st;
            std::fprintf(stderr,"SHOP_PAUSE state=%d menu=%d rid=%d\n",state->state,sd->npc_menu,state->rid);
            if(state->state==RERUNLINE)sd->npc_menu=fashion?1:2;
            else if(state->state==CLOSE)state->state=END;
            else check(state->state==STOP,"known shop suspension");
            run_script_main(state);
        }
        check(errors==0,"shop completes without failed grant");
        std::fprintf(stderr,"SHOP_STATE fashion=%d mode=%d count=%d currency=%lld\n",fashion,mode,count(itemid),(long long)nums[add_str(currency)]);
        for(auto& m:menu_text)std::fprintf(stderr,"SHOP_MENU %s\n",m.c_str());
        for(auto& m:messages)std::fprintf(stderr,"SHOP_MSG %s\n",m.c_str());
        check(count(itemid)==prior_count+(mode==0?1:0),"exact reward or no reward");
        check(nums[add_str(currency)]==(mode==0?200-cost:mode==1?0:200),"rejected purchase never charges currency");
        check(sd->status.zeny==1234567,"unrelated Zeny unchanged");
        script_free_code(code);
    }
    std::puts("SHOP_RESUME_NATIVE_OK cases=8");
}
