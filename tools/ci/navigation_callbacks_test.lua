-- Actual client Lua 5.1 callbacks and end-of-table behavior.
local directory,helper=assert(arg[1]),assert(arg[2])
for _,name in ipairs({"map","npc","mob","link","npcdistance","linkdistance","picknpc","scroll"}) do
  dofile(directory.."/navi_"..name.."_krpri.lub")
end
dofile(helper)
local count,maxdistance=0,0
for _,pair in ipairs({{Navi_Map,queryNavi_MapInfo},{Navi_Npc,queryNavi_NpcInfo},
                     {Navi_Mob,queryNavi_MobInfo},{Navi_Link,queryNavi_LinkInfo}}) do
  for i in ipairs(pair[1]) do assert(pair[2](i)~=nil);count=count+1 end
  assert(pair[2](#pair[1]+1)==nil)
end
for _,pair in ipairs({{Navi_Distance,queryNavi_Distance_Pass},{Navi_NpcDistance,queryNavi_NpcDistance_Pass}}) do
  for i=1,#pair[1],3 do
    for j,row in ipairs(pair[1][i+2]) do
      for k=1,#row-1 do
        assert(pair[2](i,j,k)~=nil);count=count+1
        maxdistance=math.max(maxdistance,row[k+1][3])
      end
      assert(pair[2](i,j,#row)==nil)
    end
  end
end
assert(maxdistance>255,"Long route distances were truncated")
print("PASS "..count.." native Lua navigation callbacks; safe end-of-table access; maximum distance "..maxdistance)
