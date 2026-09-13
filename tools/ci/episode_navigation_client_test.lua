-- Run under the actual 32-bit Lua 5.1 client runtime, from the client root.
-- arg[1] is the staged overlay; arg[2] the extracted original QuestInfo_f.lub.
table.insert = nil
local overlay, helper = assert(arg[1]), assert(arg[2])
local function equal(a,b)
  if type(a) ~= type(b) then return false end
  if type(a) ~= "table" then return a == b end
  for k,v in pairs(a) do if not equal(v,b[k]) then return false end end
  for k in pairs(b) do if a[k] == nil then return false end end
  return true
end
local function copy(t)
  if type(t) ~= "table" then return t end
  local result={}; for k,v in pairs(t) do result[k]=copy(v) end; return result
end
local reference, counts
for _,entry in ipairs({"SystemEN/OngoingQuests.lub","SystemEN/OngoingQuestInfoList.lub",
                       "System/OngoingQuestInfoList.lub","System/OngoingQuestInfoList_True.lub"}) do
  QuestInfoList=nil
  dofile(entry)
  local before=copy(QuestInfoList)
  dofile(overlay)
  local after=copy(QuestInfoList)
  dofile(overlay)
  assert(equal(after,QuestInfoList),"Overlay is not idempotent")
  for id,old in pairs(before) do
    if id ~= 17713 and id ~= 19200 then assert(equal(old,QuestInfoList[id]),"Unexpected existing quest change: "..id) end
  end
  if reference then assert(equal(reference,QuestInfoList),"Quest loader differs: "..entry) end
  reference=copy(QuestInfoList)
  dofile(helper)
  local quests, descriptions, rewards = 0,0,0
  AddOngoingDescription=function(id,text) assert(QuestInfoList[id] and type(text)=="string"); descriptions=descriptions+1 end
  AddOngoingRewardInfo=function(id,item,amount) assert(QuestInfoList[id] and type(item)=="number" and type(amount)=="number"); rewards=rewards+1 end
  for id in pairs(QuestInfoList) do
    GetOngoingQuestInfoByID(id); GetOngoingDescription(id); GetOngoingRewardInfo(id)
    quests=quests+1
  end
  assert(quests==11473, "Unexpected quest count; review this client's baseline")
  assert(GetCoolTimeQuest(18357)==1 and GetCoolTimeQuest(19200)==0)
  assert(QuestInfoList[19200].Title=="Food Procurement - Fishing")
  assert(QuestInfoList[17784].Title=="Wigner Supply Request")
  counts={quests,descriptions,rewards}
end
-- A later intentional custom guide must not be overwritten by the fill overlay.
QuestInfoList[18334]={Title="Custom quest guide",Description={"Keep this"}}
dofile(overlay)
assert(QuestInfoList[18334].Title=="Custom quest guide")
print("PASS four quest loaders; "..counts[1].." records, "..counts[2].." description callbacks, "..counts[3].." reward callbacks per loader; idempotency and existing custom guides preserved")
