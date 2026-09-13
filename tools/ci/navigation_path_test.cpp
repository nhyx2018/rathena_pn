// Compile the actual generator and heap code; only map storage and allocation
// use a small fixture. Link with --gc-sections to discard unrelated exporters.
#include <cassert>
#include <cstdarg>
#include <cstdlib>
#include <cstdio>
#include <linux/filter.h>
#if defined(__linux__) && !defined(__GLIBC__)
namespace __sanitizer { unsigned struct_sock_fprog_sz = sizeof(sock_fprog); }
#endif
#include "../../src/map/navi.cpp"

map_data map[1]{};
// The portal fixture never creates a status effect or runs combat code.
status_change::status_change() {}
status_change_entry::~status_change_entry() = default;
map_data* map_getmapdata(int16 id) { return id == 0 ? &map[0] : nullptr; }
int32 map_getcellp(map_data* m, int16 x, int16 y, cell_chk) {
    assert(x >= 0 && x < m->xs && y >= 0 && y < m->ys);
    return !m->cell[y*m->xs+x].walkable;
}
void* _mmalloc(size_t n, const char*, int32, const char*) { return std::malloc(n); }
void* _mrealloc(void* p, size_t n, const char*, int32, const char*) { return std::realloc(p,n); }
void _mfree(void* p, const char*, int32, const char*) { std::free(p); }
void ShowError(const char* text, ...) { std::fputs(text,stderr); std::abort(); }

int main() {
    map[0].xs=600; map[0].ys=5;
    std::vector<mapcell> cells(3000);
    for (auto& cell : cells) cell.walkable=true;
    map[0].cell=cells.data();
    BHEAP_INIT(g_open_set);
    navi_pos a{0,1,2}, b{0,580,2}; navi_walkpath_data path{};
    assert(navi_path_search(&path,&a,&b,CELL_CHKNOREACH));
    assert(path.path_len==579); // Former uint8 silently reported 67.
    for (int i=0;i<path.path_len;++i) assert(path.path[i]==DIR_EAST);
    auto invalid=b; invalid.x=600;
    assert(!navi_path_search(&path,&invalid,&a,CELL_CHKNOREACH));
    assert(!navi_path_search(&path,&a,&invalid,CELL_CHKNOREACH));
    invalid=b; invalid.y=5;
    assert(!navi_path_search(&path,&a,&invalid,CELL_CHKNOREACH));
    invalid=a; invalid.m=-1;
    assert(!navi_path_search(&path,&invalid,&b,CELL_CHKNOREACH));
    // Three blocked columns divide the map. A two-cell talk approach can
    // reach the NPC in the wall; a one-cell portal touch area cannot.
    for(int y=0;y<5;++y) for(int x=19;x<=21;++x) cells[y*600+x].walkable=false;
    b={0,20,2};
    assert(!navi_path_search(&path,&a,&b,CELL_CHKNOREACH));
    assert(!navi_approach_search(&path,a,b,{0,0},{1,1}));
    assert(navi_approach_search(&path,a,b,{0,0},{2,2}));
    assert(path.path_len==17);
    assert(!navi_approach_search(&path,a,b,{0,0},{0,2}));
    b={0,30,2};
    assert(!navi_approach_search(&path,a,b,{3,3},{3,3})); // Never crosses a wall.
    npc_data portal{}; portal.subtype=NPCTYPE_WARP;
    portal.u.warp.xs=1; portal.u.warp.ys=2;
    navi_link link{}; link.npc=&portal;
    assert(navi_link_area(link)==std::make_pair(1,2));
    portal.subtype=NPCTYPE_SCRIPT; portal.class_=JT_WARPNPC;
    portal.u.scr.xs=2; portal.u.scr.ys=1;
    assert(navi_link_area(link)==std::make_pair(2,1));
    BHEAP_CLEAR(g_open_set);
    std::puts("PASS native navigation: long paths, bounds, blocked NPC approaches, rectangular touch areas, disconnected rooms");
}
