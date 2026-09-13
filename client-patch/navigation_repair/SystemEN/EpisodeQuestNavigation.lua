-- PN Episode 21 quest-book compatibility. GPL-3.0-or-later.
-- Only supply records absent from the installed canonical quest table.
-- Sources and exact NPC anchors: EpisodeQuestNavigation.json.
local function guide(id,title,summary,description,timed)
  if QuestInfoList[id] ~= nil then return end
  QuestInfoList[id] = {Title=title,IconName="ico_nq.bmp",Summary=summary,Description=description}
  if timed then QuestInfoList[id].CoolTimeQuest=1 end
end

guide(17752,"Cult Infiltration","Ask Lehar about the cult.",{"Ask Lehar about the cult. <NAVI>[Lehar]<INFO>jor_mbase,214,316,0,101,0</INFO></NAVI>"},false)
guide(17753,"Cult Infiltration","Hear Lyriq's report.",{"Hear Lyriq's report. <NAVI>[Lyriq]<INFO>jor_mbase,185,311,0,101,0</INFO></NAVI>"},false)
guide(17754,"Cult Infiltration","Consult the Wigner archive.",{"Consult the Wigner archive. <NAVI>[Lalaila Wigner]<INFO>jalbe_in,56,138,0,101,0</INFO></NAVI>"},false)
guide(17755,"Cult Infiltration","Examine the dusty box upstairs.",{"Examine the dusty box upstairs. <NAVI>[Dusty Box]<INFO>jalbe_in,73,187,0,101,0</INFO></NAVI>"},false)
guide(17756,"Cult Infiltration","Show the Walter manifest to Maristella.",{"Show the Walter manifest to Maristella. <NAVI>[Maristella Walter]<INFO>jalbe_in,68,46,0,101,0</INFO></NAVI>"},false)
guide(17757,"Cult Infiltration","Report your findings to Ivan.",{"Report your findings to Ivan. <NAVI>[Ivan]<INFO>jor_mbase,233,277,0,101,0</INFO></NAVI>"},false)
guide(17758,"Recruiting Talent for Success","Take the small boat to Scale Island.",{"Take the small boat to Scale Island. <NAVI>[Small Boat]<INFO>jor_mbase,124,27,0,101,0</INFO></NAVI>"},false)
guide(17759,"Recruiting Talent for Success","Speak with Tan on Scale Island.",{"Speak with Tan on Scale Island. <NAVI>[Tan]<INFO>jor_crk_p,71,86,0,101,0</INFO></NAVI>"},false)
guide(17760,"Recruiting Talent for Success","Ask Ivan to arrange the high-priest disguise.",{"Ask Ivan to arrange the high-priest disguise. <NAVI>[Ivan]<INFO>jor_mbase,166,302,0,101,0</INFO></NAVI>"},false)
guide(17761,"2nd Floor Cult Infiltration","Enter the first temple safe spot",{"Approach the marked spot on temple floor 1. <NAVI>[First prayer room]<INFO>jor_tmple1,186,72,0,101,0</INFO></NAVI>"},false)
guide(17762,"2nd Floor Cult Infiltration","Gather the three believers' reports",{"Speak with Ivan, then return to temple floor 1. <NAVI>[Ivan]<INFO>luna_sf2,113,257,0,101,0</INFO></NAVI>","Visit the second safe spot and speak with the believer. <NAVI>[Second prayer room]<INFO>jor_tmple1,110,190,0,101,0</INFO></NAVI>","Visit the third safe spot after the first report. <NAVI>[Third prayer room]<INFO>jor_tmple1,186,228,0,101,0</INFO></NAVI>","Visit the fourth safe spot after the second report. <NAVI>[Fourth prayer room]<INFO>jor_tmple1,238,268,0,101,0</INFO></NAVI>"},false)
guide(17763,"2nd Floor Cult Infiltration","Report the three believers' accounts to Tris.",{"Report the three believers' accounts to Tris. <NAVI>[Tris]<INFO>jor_mbase,143,272,0,101,0</INFO></NAVI>"},false)
guide(17764,"2nd Floor Cult Infiltration","Complete Gimli Infiltration",{"Use the fourth safe spot to reach the disguised guard. <NAVI>[Fourth prayer room]<INFO>jor_tmple1,238,268,0,101,0</INFO></NAVI>","Form a party and enter Gimli Infiltration. Follow Nadoyo through both floors. Re-enter through this guard after a disconnect. <NAVI>[Disguised Temple Guard]<INFO>luna_sf2,187,254,0,101,0</INFO></NAVI>"},false)
guide(17765,"2nd Floor Cult Infiltration","Report the escape to Nadoyo",{"Use the northern safe spot after leaving Gimli. <NAVI>[Northern safe spot]<INFO>jor_raise1,322,69,0,101,0</INFO></NAVI>","Speak with Nadoyo in the safe area. <NAVI>[Nadoyo]<INFO>luna_sf1,48,265,0,101,0</INFO></NAVI>"},false)
guide(17766,"2nd Floor Cult Infiltration","Deliver Nadoyo's infiltration report.",{"Deliver Nadoyo's infiltration report. <NAVI>[Tris]<INFO>jor_mbase,143,272,0,101,0</INFO></NAVI>"},false)
guide(17767,"2nd Floor Cult Infiltration","Speak with Wilhelm upstairs.",{"Speak with Wilhelm upstairs. <NAVI>[Wilhelm]<INFO>mbase_in,116,186,0,101,0</INFO></NAVI>"},false)
guide(17768,"2nd Floor Cult Infiltration","Hear Reinhardt's account of the Ghost Ship.",{"Hear Reinhardt's account of the Ghost Ship. <NAVI>[Reinhardt]<INFO>mbase_in,120,186,0,101,0</INFO></NAVI>"},false)
guide(17769,"Ghost Ship Report","Report to Maristella inside the Alberta office.",{"Report to Maristella inside the Alberta office. <NAVI>[Maristella Walter]<INFO>jalbe_in,68,46,0,101,0</INFO></NAVI>"},false)
guide(17770,"Lugenburg Brothers","Help the Lugenburg brothers reconcile",{"Continue the brothers' discussion with this NPC. <NAVI>[Reinhardt]<INFO>mbase_in,118,186,0,101,0</INFO></NAVI>"},false)
guide(17771,"Lugenburg Brothers","Help the Lugenburg brothers reconcile",{"Continue the brothers' discussion with this NPC. <NAVI>[Wilhelm]<INFO>jor_mbase,140,201,0,101,0</INFO></NAVI>"},false)
guide(17772,"Lugenburg Brothers","Help the Lugenburg brothers reconcile",{"Continue the brothers' discussion with this NPC. <NAVI>[Reinhardt]<INFO>mbase_in,118,186,0,101,0</INFO></NAVI>"},false)
guide(17773,"Lugenburg Brothers","Help the Lugenburg brothers reconcile",{"Continue the brothers' discussion with this NPC. <NAVI>[Tris]<INFO>jor_mbase,197,277,0,101,0</INFO></NAVI>"},false)
guide(17774,"Lugenburg Brothers","Help the Lugenburg brothers reconcile",{"Continue the brothers' discussion with this NPC. <NAVI>[Reinhardt]<INFO>mbase_in,118,186,0,101,0</INFO></NAVI>"},false)
guide(17775,"Lugenburg Brothers","Help the Lugenburg brothers reconcile",{"Continue the brothers' discussion with this NPC. <NAVI>[Wilhelm]<INFO>jor_mbase,140,201,0,101,0</INFO></NAVI>"},false)
guide(17776,"Lugenburg Brothers","Help the Lugenburg brothers reconcile",{"Continue the brothers' discussion with this NPC. <NAVI>[Tris]<INFO>jor_mbase,197,277,0,101,0</INFO></NAVI>"},false)
guide(17777,"Safe Escape Route 1","Defeat 300 monsters in Northern Raised Land (jor_raise1)",{"Defeat 300 monsters on Northern Raised Land (jor_raise1), then report to Wilhelm. Patrols reset at 04:00 server time. <NAVI>[Wilhelm]<INFO>jor_mbase,140,201,0,101,0</INFO></NAVI>"},false)
guide(17778,"Safe Escape Route 2","Defeat 300 monsters in Southern Raised Land (jor_raise2)",{"Defeat 300 monsters on Southern Raised Land (jor_raise2), then report to Wilhelm. Patrols reset at 04:00 server time. <NAVI>[Wilhelm]<INFO>jor_mbase,140,201,0,101,0</INFO></NAVI>"},false)
guide(17781,"Supply Procurement","Supply Procurement unlocked",{"Choose a family supply contract after completing Episode 21. One family contract may be completed per day; reset is at 04:00 server time. <NAVI>[Mandel]<INFO>jor_mbase,219,315,0,101,0</INFO></NAVI>"},false)
guide(17782,"Gaebolg Supply Request","Deliver supplies for Gaebolg",{"Deliver 10 units of item 1001629 for the Gaebolg family. Mandel confirms the required material. One family contract per day; reset is at 04:00 server time. <NAVI>[Mandel]<INFO>jor_mbase,219,315,0,101,0</INFO></NAVI>"},false)
guide(17783,"Nerius Supply Request","Deliver supplies for Nerius",{"Deliver 10 units of item 1001648 for the Nerius family. Mandel confirms the required material. One family contract per day; reset is at 04:00 server time. <NAVI>[Mandel]<INFO>jor_mbase,219,315,0,101,0</INFO></NAVI>"},false)
guide(17784,"Wigner Supply Request","Deliver supplies for Wigner",{"Deliver 10 units of item 1001642 for the Wigner family. Mandel confirms the required material. One family contract per day; reset is at 04:00 server time. <NAVI>[Mandel]<INFO>jor_mbase,219,315,0,101,0</INFO></NAVI>"},false)
guide(17785,"Heine Supply Request","Deliver supplies for Heine",{"Deliver 10 units of item 1001639 for the Heine family. Mandel confirms the required material. One family contract per day; reset is at 04:00 server time. <NAVI>[Mandel]<INFO>jor_mbase,219,315,0,101,0</INFO></NAVI>"},false)
guide(17786,"Lugenburg Supply Request","Deliver supplies for Lugenburg",{"Deliver 10 units of item 1001637 for the Lugenburg family. Mandel confirms the required material. One family contract per day; reset is at 04:00 server time. <NAVI>[Mandel]<INFO>jor_mbase,219,315,0,101,0</INFO></NAVI>"},false)
guide(17787,"Walter Supply Request","Deliver supplies for Walter",{"Deliver 10 units of item 1001646 for the Walter family. Mandel confirms the required material. One family contract per day; reset is at 04:00 server time. <NAVI>[Mandel]<INFO>jor_mbase,219,315,0,101,0</INFO></NAVI>"},false)
guide(17788,"Richard Supply Request","Deliver supplies for Richard",{"Deliver 10 units of item 1001645 for the Richard family. Mandel confirms the required material. One family contract per day; reset is at 04:00 server time. <NAVI>[Mandel]<INFO>jor_mbase,219,315,0,101,0</INFO></NAVI>"},false)
guide(18334,"Detected Rift on the North","Join the Scale Island expedition",{"Begin the expedition. Requires Base Level 230 and completion of Episode 20. <NAVI>[Shufapa]<INFO>jor_tail,233,41,0,101,0</INFO></NAVI>"},false)
guide(18335,"Rift on Scale Island","Examine the present-day rift",{"Speak with Nyar and cross the rift. <NAVI>[Nyar]<INFO>jor_crk,105,108,0,101,0</INFO></NAVI>"},false)
guide(18336,"First Meeting","Meet Nyar in the past",{"Speak with Nyar on the past Scale Island. <NAVI>[Nyar]<INFO>jor_crk_p,105,108,0,101,0</INFO></NAVI>"},false)
guide(18337,"Lunaforma","Meet Ivan",{"Introduce yourself to Ivan and enter the resistance route. <NAVI>[Ivan]<INFO>jor_crk_p,100,95,0,101,0</INFO></NAVI>"},false)
guide(18338,"Gathering Eyewitness","Resistance investigation record",{"This is a legacy investigation record. Continue the active Gaebolg Resistance stage in your quest log. <NAVI>[Tris]<INFO>jor_mbase,56,152,0,101,0</INFO></NAVI>"},false)
guide(18343,"Find Tan and Nadoyo","Find Tan and Nadoyo",{"Enter the Rock Crevice in Northern Raised Land. <NAVI>[Rock Crevice]<INFO>jor_raise1,198,189,0,101,0</INFO></NAVI>","Speak with Nadoyo inside the safe area. <NAVI>[Nadoyo]<INFO>luna_sf1,47,264,0,101,0</INFO></NAVI>"},false)
guide(18344,"Suspicion Location in the Temple","Investigate the sealed temple chamber",{"Enter the Decorative Door in Northern Raised Land. <NAVI>[Decorative Door]<INFO>jor_raise1,128,323,0,101,0</INFO></NAVI>","Listen to the cult priest inside. <NAVI>[Cult Priest]<INFO>jor_tmple1,170,304,0,101,0</INFO></NAVI>"},false)
guide(18345,"Serpent's Lair?","Warn Tris about the serpent",{"Ask Nadoyo to return you to command. <NAVI>[Nadoyo]<INFO>jor_tmple1,174,304,0,101,0</INFO></NAVI>","Report what you learned. <NAVI>[Tris]<INFO>jor_mbase,203,186,0,101,0</INFO></NAVI>"},false)
guide(18346,"Excluded from the Final Battle","Meet Nyar beside Heine's room",{"Approach the small door upstairs. <NAVI>[Small Door]<INFO>mbase_in,75,126,0,101,0</INFO></NAVI>","Discuss how to join the battle without changing history. <NAVI>[Nyar]<INFO>mbase_in,80,126,0,101,0</INFO></NAVI>"},false)
guide(18347,"I can't miss it!","Return to Nadoyo in the temple",{"Enter through the Decorative Door. <NAVI>[Decorative Door]<INFO>jor_raise1,128,323,0,101,0</INFO></NAVI>","Hear Nadoyo's plan. <NAVI>[Nadoyo]<INFO>jor_tmple1,174,304,0,101,0</INFO></NAVI>"},false)
guide(18348,"Join the Final Battle","Complete the story Final Battle",{"Enter the story Final Battle. Activate the four channels, finish the encounters, then speak with Nyar at the end. Re-entry uses this tablet. <NAVI>[Heine's Tablet]<INFO>jor_tmple1,178,304,0,101,0</INFO></NAVI>"},false)
guide(18349,"Cat Led Adventures","Follow Nyar's altar lead",{"Speak with Nyar outside the final battle. <NAVI>[Nyar]<INFO>jor_tmple1,182,304,0,101,0</INFO></NAVI>"},false)
guide(18350,"Suspicious Book of Gimli","Read the Suspicious Book",{"Read the book on the past Scale Island. <NAVI>[Suspicious Book]<INFO>jor_crk_p,87,95,0,101,0</INFO></NAVI>"},false)
guide(18351,"Shining Door","Enter and complete Secret Altar",{"Enter Secret Altar and follow Lehar through the encounters. Finish the Giant Egg dialogue to receive story credit. Re-enter through this door if needed. <NAVI>[Shining Door]<INFO>jor_crk_p,90,95,0,101,0</INFO></NAVI>"},false)
guide(18352,"Finally, A Real Mission!","Enter and complete Secret Altar",{"Enter Secret Altar and follow Lehar through the encounters. Finish the Giant Egg dialogue to receive story credit. Re-enter through this door if needed. <NAVI>[Shining Door]<INFO>jor_crk_p,90,95,0,101,0</INFO></NAVI>"},false)
guide(18353,"Successfully Blocked the Source","Report that the source is blocked",{"Speak with Nyar after leaving Secret Altar. <NAVI>[Nyar]<INFO>jor_crk_p,83,95,0,101,0</INFO></NAVI>"},false)
guide(18354,"Heine's Gift","Find Heine's gift",{"Take the small boat to the hidden Lunaforma dock. <NAVI>[Small Boat]<INFO>jor_crk_p,80,90,0,101,0</INFO></NAVI>","Search the bushes and leave room for the costume. <NAVI>[Bushes]<INFO>luna_sf1,44,40,0,101,0</INFO></NAVI>"},false)
guide(18355,"Return to Scale Island","Return to Scale Island",{"Return to Nyar on the past Scale Island. <NAVI>[Nyar]<INFO>jor_crk_p,83,95,0,101,0</INFO></NAVI>"},false)
guide(18356,"Time to Confirm Casualty","Check the present-day sanctuary",{"Use the disturbance at the present-day rift. <NAVI>[Rift Disturbance]<INFO>jor_crk,137,138,0,101,0</INFO></NAVI>","Speak to Nyar's clone at the sanctuary entrance. <NAVI>[Nyar Clone]<INFO>jor_twig,187,198,0,101,0</INFO></NAVI>"},false)
guide(18357,"Settling the Curse","Wait 10 minutes for the curse to settle",{"Wait until this quest timer expires, then speak to the clone again. <NAVI>[Nyar Clone]<INFO>jor_twig,187,198,0,101,0</INFO></NAVI>"},true)
guide(18358,"Lasgand?","Confirm Lasgand's condition",{"Enter Silent Sanctuary, follow Aurelie, examine Lasgand, then finish Aurelie's final dialogue. Re-entry uses this clone. <NAVI>[Nyar Clone]<INFO>jor_twig,187,198,0,101,0</INFO></NAVI>"},false)
guide(18359,"Butterfly Effect","Report the sanctuary findings",{"Speak to the clone after leaving Silent Sanctuary. <NAVI>[Nyar Clone]<INFO>jor_twig,187,198,0,101,0</INFO></NAVI>"},false)
guide(18361,"Nyar's Primal Pouch","Episode 21 completion record",{"The campaign is complete. Normal Final Battle is unlocked. Hard mode requires 1,000 reputation with each of the seven families. <NAVI>[Nyar]<INFO>jor_crk,140,138,0,101,0</INFO></NAVI>"},false)
guide(19198,"Vallen Wok","Food procurement unlocked",{"Ask Vallen Wok for the current food assignment. Deliveries reset at 04:00 server time. <NAVI>[Volunteer Vallen Wok]<INFO>jor_mbase,211,280,0,101,0</INFO></NAVI>"},false)
guide(19201,"Food Procurement(Herb Gathering)","Gather 10 Wide Grass",{"Bring 10 Wide Grass (item 1001625) to Vallen Wok. <NAVI>[Volunteer Vallen Wok]<INFO>jor_mbase,211,280,0,101,0</INFO></NAVI>"},false)
guide(23240,"Gaebolg Resistance","Follow Ivan to the resistance",{"Meet Ivan in the safe area before entering Lunaforma. <NAVI>[Ivan]<INFO>luna_sf1,258,151,0,101,0</INFO></NAVI>"},false)
guide(23241,"Gaebolg Resistance","Meet the Resistance Soldier",{"Speak to the soldier at the west gate. <NAVI>[Resistance Soldier]<INFO>jor_mbase,54,155,0,101,0</INFO></NAVI>"},false)
guide(23242,"Gaebolg Resistance","Introduce yourself to Tris",{"Hear Tris's instructions. <NAVI>[Tris]<INFO>jor_mbase,56,152,0,101,0</INFO></NAVI>"},false)
guide(23243,"Gaebolg Resistance","Complete the resistance introductions",{"Start with Tan at the west gate. <NAVI>[Tan]<INFO>jor_mbase,57,150,0,101,0</INFO></NAVI>","Meet Tan at the eastern tent. <NAVI>[Tan]<INFO>jor_mbase,313,106,0,101,0</INFO></NAVI>","Inspect the reports inside. <NAVI>[Pile of Documents]<INFO>mbase_in,299,126,0,101,0</INFO></NAVI>","Speak with Valdaris. <NAVI>[Valdaris]<INFO>mbase_in,302,123,0,101,0</INFO></NAVI>","Meet Richard in the central barracks. <NAVI>[Richard]<INFO>mbase_in,167,128,0,101,0</INFO></NAVI>","Speak to Lee inside. <NAVI>[Lee]<INFO>mbase_in,167,79,0,101,0</INFO></NAVI>","Finish the introduction with Lee outside. <NAVI>[Lee]<INFO>jor_mbase,163,196,0,101,0</INFO></NAVI>"},false)
guide(23247,"Calculating Profit and Loss","Hunt 10 Skipskippers and bring 1 Bright Eye",{"Hunt 10 Skipskippers in Southern Raised Land (jor_raise2), bring 1 Bright Eye, then report to Tris. <NAVI>[Tris]<INFO>jor_mbase,168,200,0,101,0</INFO></NAVI>"},false)
guide(23248,"Calculating Profit and Loss","The sea route to Alberta is open",{"Continue with Nillem, then help Yohan and Iana Operta in Old Alberta. <NAVI>[Nillem]<INFO>jor_albe,192,209,0,101,0</INFO></NAVI>"},false)
guide(23249,"Black-Haired Beast","Examine the failing tablet.",{"Examine the failing tablet. <NAVI>[Heine's Tablet]<INFO>mbase_in,71,126,0,101,0</INFO></NAVI>"},false)
guide(23250,"Black-Haired Beast","Bring 2 Vellelopy from Velellings in Northern Raised Land.",{"Bring 2 Vellelopy from Velellings in Northern Raised Land. <NAVI>[Heine's Tablet]<INFO>mbase_in,71,126,0,101,0</INFO></NAVI>"},false)
guide(23251,"Black-Haired Beast","Listen to Heine's story.",{"Listen to Heine's story. <NAVI>[Heine's Tablet]<INFO>mbase_in,71,126,0,101,0</INFO></NAVI>"},false)
guide(23252,"Black-Haired Beast","Finish repairing the tablet; leave room for the repaired item.",{"Finish repairing the tablet; leave room for the repaired item. <NAVI>[Heine's Tablet]<INFO>mbase_in,71,126,0,101,0</INFO></NAVI>"},false)
guide(23253,"Black-Haired Beast","Report to Tris",{"Return with the repaired tablet. <NAVI>[Tris]<INFO>jor_mbase,203,186,0,101,0</INFO></NAVI>"},false)
guide(23254,"Black-Haired Beast","Speak to Nadoyo",{"Ask Nadoyo about the serpent. <NAVI>[Nadoyo]<INFO>jor_mbase,209,186,0,101,0</INFO></NAVI>"},false)
guide(23255,"Black-Haired Beast","Collect three eyewitness reports",{"Hear the wounded soldier. <NAVI>[Wounded Soldier]<INFO>jor_mbase,62,194,0,101,0</INFO></NAVI>","Hear the exhausted soldier. <NAVI>[Exhausted Soldier]<INFO>jor_mbase,186,250,0,101,0</INFO></NAVI>","Hear the escapee. <NAVI>[Cult Escapee]<INFO>jor_mbase,216,297,0,101,0</INFO></NAVI>","Return after collecting all three reports. <NAVI>[Tris]<INFO>jor_mbase,203,186,0,101,0</INFO></NAVI>"},false)
guide(24019,"We're the Mercenaries, but...","Meet the four mercenary members",{"Speak with this mercenary. <NAVI>[Mercenary Member]<INFO>jor_mbase,300,151,0,101,0</INFO></NAVI>","Speak with this mercenary. <NAVI>[Mercenary Member]<INFO>jor_mbase,198,251,0,101,0</INFO></NAVI>","Speak with this mercenary. <NAVI>[Mercenary Member]<INFO>jor_mbase,133,128,0,101,0</INFO></NAVI>","Speak with this mercenary. <NAVI>[Mercenary Member]<INFO>jor_mbase,248,103,0,101,0</INFO></NAVI>","Report after speaking to all four members to unlock contracts. <NAVI>[Valdaris]<INFO>mbase_in,304,123,0,101,0</INFO></NAVI>"},false)
guide(24031,"Fresh Food!","Bring 10 Skipskipper Fins and 10 Thick Flesh.",{"Bring 10 Skipskipper Fins and 10 Thick Flesh. Return to Valdaris. Contracts reset at 04:00 server time. <NAVI>[Valdaris]<INFO>mbase_in,304,123,0,101,0</INFO></NAVI>"},false)
guide(24033,"Clamshell for Injuries!","Defeat 50 Scallegs in Northern Raised Land.",{"Defeat 50 Scallegs in Northern Raised Land. Return to Valdaris. Contracts reset at 04:00 server time. <NAVI>[Valdaris]<INFO>mbase_in,304,123,0,101,0</INFO></NAVI>"},false)
guide(24035,"For the Children.","Defeat 50 Velellings in Northern Raised Land.",{"Defeat 50 Velellings in Northern Raised Land. Return to Valdaris. Contracts reset at 04:00 server time. <NAVI>[Valdaris]<INFO>mbase_in,304,123,0,101,0</INFO></NAVI>"},false)
guide(24037,"Clean Finish(1)","Defeat 300 monsters on Jormungandr Temple floor 1.",{"Defeat 300 monsters on Jormungandr Temple floor 1. Return to Valdaris. Contracts reset at 04:00 server time. <NAVI>[Valdaris]<INFO>mbase_in,304,123,0,101,0</INFO></NAVI>"},false)
guide(24039,"Clean Finish(2)","Defeat 300 monsters on Jormungandr Temple floor 2.",{"Defeat 300 monsters on Jormungandr Temple floor 2. Return to Valdaris. Contracts reset at 04:00 server time. <NAVI>[Valdaris]<INFO>mbase_in,304,123,0,101,0</INFO></NAVI>"},false)

-- Correct known base-client records reused by this server's active quests.
if QuestInfoList[19200] and QuestInfoList[19200].Title == "RPS with Troy" then
  QuestInfoList[19200] = {
    Title="Food Procurement - Fishing", IconName="ico_dq.bmp", Summary="Deliver 10 requested food items",
    Description={"Ask Vallen Wok which food he requested, gather 10 of that item, then return. <NAVI>[Volunteer Vallen Wok]<INFO>jor_mbase,211,280,0,101,0</INFO></NAVI>. Deliveries reset at 04:00 server time."}
  }
end
if QuestInfoList[17713] then
  local q = QuestInfoList[17713]
  for i,line in ipairs(q.Description or {}) do
    if string.find(line,"icas_in2,31,116,0,101,0",1,true) then
      q.Description[i] = "Speak to <NAVI>[Nadyagand]<INFO>icas_in2,33,114,0,101,0</INFO></NAVI> again to receive the Snake Strawberry request."
    end
  end
end
