// PN account bank. GPL-3.0-or-later.
#pragma once
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <winsock2.h>
#include <windows.h>
#include <cstdint>
#include "../../src/custom/bank_protocol.hpp"

constexpr UINT BANK_OPEN = WM_APP + 21, BANK_RESULT = WM_APP + 22, BANK_SESSION = WM_APP + 23;
constexpr UINT BANK_REMOTE_OPEN = WM_APP + 24;
struct BankResult { pn_bank::Reply state; LONG generation = 0; bool connected = false; };
void bank_install_transport(HWND panel);
bool bank_submit(HWND panel, const pn_bank::Reply& state, uint32_t action, int64_t amount, uint64_t sequence);
bool bank_authenticated();
bool bank_current_generation(LONG generation, bool active = true);
bool bank_connection_ready();
HWND bank_find_game_window();
int bank_window_main(HINSTANCE module, bool preview);
