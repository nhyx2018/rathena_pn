// The Python runner inserts both production callbacks below, unchanged.
// DNS, socket allocation and handshake recipients are test doubles.
#include <arpa/inet.h>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

using int32 = int32_t;
using uint32 = uint32_t;
using uint16 = uint16_t;
#define TIMER_FUNC(name) int32 name(int tid, int64_t tick, int id, intptr_t data)
#define FIFOSIZE_SERVERLINK 1024
struct Socket {
    int32 (*func_parse)(int32) = nullptr;
    struct { bool server = false; } flag;
};
Socket socket_double;
Socket* session[16]{};
struct {
    char login_ip_str[128] = "login";
    uint32 login_ip = 0;
    uint16 login_port = 6900;
    char userid[24] = "fixture", passwd[24] = "fixture-only";
    uint32 char_ip = 0xc0a80a12;
    uint16 char_port = 6121;
    char server_name[20] = "Fixture";
    uint16 char_maintenance = 0, char_new_display = 1;
} charserv_config;
int32 login_fd = -1, char_fd = -1, chrif_state = 0;
bool login_connected = false, chrif_connected = false;
uint32 char_ip = 0;
uint16 char_port = 6121;
char char_ip_str[128] = "char";
uint32 dns_answer = 0, connected_ip = 0;
int dns_calls = 0, connect_calls = 0, allocated_fd = -1, map_handshakes = 0;
uint16 connected_port = 0;
std::string dns_name;
std::array<unsigned char, 128> fifo{};
int written = 0, checks = 0, failures = 0;

void expect(bool condition, const char* label) {
    ++checks;
    if (!condition) { ++failures; std::fprintf(stderr, "FAIL: %s\n", label); }
}
template<typename... Args> void ShowInfo(const char*, Args...) {}
template<typename... Args> void ShowStatus(const char*, Args...) {}
template<typename... Args> void ShowWarning(const char*, Args...) {}
uint32 host2ip(const char* name) {
    ++dns_calls; dns_name = name; return dns_answer;
}
int32 chlogif_isconnected() { return login_connected; }
int32 chrif_isconnected() { return chrif_state == 2; }
int32 chlogif_parse(int32) { return 0; }
int32 chrif_parse(int32) { return 0; }
int32 make_connection(uint32 ip, uint16 port, bool silent, int timeout) {
    ++connect_calls; connected_ip = ip; connected_port = port;
    expect(!silent && timeout == 10, "preserve connection options");
    if (allocated_fd >= 0) session[allocated_fd] = &socket_double;
    return allocated_fd;
}
void realloc_fifo(int32, int, int) {}
void chrif_connect(int32) { ++map_handshakes; chrif_state = 1; }
template<typename T> struct Field {
    size_t offset;
    void operator=(T value) { std::memcpy(fifo.data() + offset, &value, sizeof(value)); }
};
template<typename T> T read_field(size_t offset) {
    T value; std::memcpy(&value, fifo.data() + offset, sizeof(value)); return value;
}
#define WFIFOHEAD(fd, size) ((void)0)
#define WFIFOW(fd, offset) Field<uint16>{offset}
#define WFIFOL(fd, offset) Field<uint32>{offset}
#define WFIFOP(fd, offset) (fifo.data() + offset)
#define WFIFOSET(fd, size) (written = size)

// @production:chlogif_check_connect_logserver
// @production:check_connect_char_server

void reset() {
    login_fd = char_fd = -1; login_connected = chrif_connected = false;
    chrif_state = 0; socket_double = {};
    for (auto& ptr : session) ptr = nullptr;
    dns_calls = connect_calls = map_handshakes = written = 0;
    allocated_fd = -1; connected_ip = connected_port = 0; dns_name.clear(); fifo.fill(0);
    charserv_config.login_ip = char_ip = 0xac130002;
    std::strcpy(charserv_config.login_ip_str, "login");
    std::strcpy(char_ip_str, "char");
}

int main() {
    for (bool map : {false, true}) {
        auto call = [map] {
            if (map) check_connect_char_server(0, 0, 0, 0);
            else chlogif_check_connect_logserver(0, 0, 0, 0);
        };
        auto cached = [map] { return map ? char_ip : charserv_config.login_ip; };
        auto hostname = [map] { return map ? char_ip_str : charserv_config.login_ip_str; };
        const uint16 port = map ? 6121 : 6900;

        reset(); dns_answer = 0xac130006; call();
        expect(dns_calls == 1 && dns_name == (map ? "char" : "login"), "resolve configured service hostname");
        expect(connect_calls == 1 && connected_ip == dns_answer && connected_port == port,
               "reconnect to moved service instead of previous container address");
        expect(cached() == dns_answer, "cache refreshed address");
        dns_answer = 0xac130009; call();
        expect(dns_calls == 2 && connected_ip == dns_answer, "refresh again after failed TCP connection");

        reset(); dns_answer = 0; call();
        expect(dns_calls == 1 && connect_calls == 0, "DNS failure must not contact stale address");
        expect(cached() == 0xac130002, "DNS failure must not replace cached address with zero");
        expect(written == 0 && map_handshakes == 0, "no authentication while DNS is unresolved");
        dns_answer = 0xac130007; allocated_fd = 7; call();
        expect(connect_calls == 1 && connected_ip == dns_answer, "recover after temporary DNS failure");
        expect(session[7] && session[7]->flag.server, "mark successful upstream as server link");
        expect(session[7] && session[7]->func_parse == (map ? chrif_parse : chlogif_parse),
               "preserve upstream parser");
        if (map) {
            expect(map_handshakes == 1 && !chrif_connected && chrif_state == 1,
                   "send map handshake and wait for acknowledgement");
        } else {
            expect(written == 86 && read_field<uint16>(0) == 0x2710, "preserve login handshake packet");
            expect(std::memcmp(fifo.data() + 2, charserv_config.userid, 24) == 0 &&
                   std::memcmp(fifo.data() + 26, charserv_config.passwd, 24) == 0,
                   "preserve interserver authentication");
            expect(read_field<uint32>(54) == htonl(charserv_config.char_ip) &&
                   read_field<uint16>(58) == htons(charserv_config.char_port),
                   "preserve client-facing character endpoint");
        }

        reset(); login_connected = true; char_fd = 7; session[7] = &socket_double;
        chrif_state = 2; dns_answer = 0xac13000a; call();
        expect(dns_calls == 0 && connect_calls == 0, "do not disturb an active upstream connection");

        reset(); std::strcpy(hostname(), "192.168.10.18"); dns_answer = 0xc0a80a12;
        charserv_config.login_ip = char_ip = dns_answer; call();
        expect(connected_ip == dns_answer && connected_port == port,
               "literal address configuration still connects");

        reset(); hostname()[0] = '\0'; call();
        expect(dns_calls == 0 && connect_calls == 1 && connected_ip == cached(),
               "preserve numeric fallback when no hostname was configured");
    }
    std::printf("{\"passed\":%s,\"checks\":%d,\"failures\":%d}\n", failures ? "false" : "true", checks, failures);
    return failures ? 1 : 0;
}
